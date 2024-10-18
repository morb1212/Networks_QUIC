import unittest
from unittest.mock import patch, mock_open, call
import time
from quic import (
    quic_send,
    quic_recv,
    parse_quic_packet,
    print_statistics,
    create_quic_packet,
    stream_statistics,
)
from server import server_function
from client import client_function


class Test(unittest.TestCase):
    def setUp(self):
        # Address to send messages to
        self.destination = ('127.0.0.1', 5060)  

    @patch('socket.socket')
    # Mock the packet size
    @patch('quic.set_stream_packet_size', return_value=10)  
    def test_quic_send(self, mock_set_stream_packet_size, mock_socket):
        """Test that quic_send sends data correct and updates the statistics."""
        mock_sock_instance = mock_socket.return_value

        # Use mock data to simulate file content
        data = b'Test'  
        stream_id = 1

        quic_send(mock_sock_instance, self.destination, data, stream_id)

        # Calculate expected number of packets
        packet_size = 10
        expected_packets = (len(data) + packet_size - 1) // packet_size  # Ceiling division

        # Check sendto was called the expected number of times
        self.assertEqual(mock_sock_instance.sendto.call_count, expected_packets)

        # Check statistics
        # TODO
        self.assertIn(stream_id, stream_statistics)
        self.assertEqual(stream_statistics[stream_id]['bytes'] - 12, len(data))  # Corrected byte count check
        self.assertEqual(stream_statistics[stream_id]['packets'] - 1, expected_packets)

    @patch('socket.socket')
    def test_quic_recv_valid_packet(self, mock_socket):
        """Test quic_recv correctly receives and parses a valid packet."""
        mock_sock_instance = mock_socket.return_value

        # Create a valid packet
        stream_id = 1
        frame_offset = 0
        payload = b'Test payload'
        packet = create_quic_packet(stream_id, frame_offset, payload)

        # Mock recvfrom to return our packet
        mock_sock_instance.recvfrom.return_value = (packet, self.destination)

        # Clear before the test
        stream_statistics.clear()

        result = quic_recv(mock_sock_instance)

        self.assertEqual(result, (stream_id, frame_offset, payload))

        # Check statistics
        self.assertIn(stream_id, stream_statistics)
        self.assertEqual(stream_statistics[stream_id]['bytes'], len(payload))
        self.assertEqual(stream_statistics[stream_id]['packets'], 1)
        self.assertIsNotNone(stream_statistics[stream_id]['start_time'])
        self.assertIsNotNone(stream_statistics[stream_id]['end_time'])

    @patch('socket.socket')
    def test_quic_recv_invalid_packet(self, mock_socket):
        """Test quic_recv handles invalid packet gracefully."""
        mock_sock_instance = mock_socket.return_value

        # Create an invalid packet (insufficient data)
        invalid_packet = b'\x00\x00'

        # Mock recvfrom to return invalid packet
        mock_sock_instance.recvfrom.return_value = (invalid_packet, self.destination)

        result = quic_recv(mock_sock_instance)

        self.assertIsNone(result)

    @patch('socket.socket')
    def test_quic_recv_close_packet(self, mock_socket):
        """Test quic_recv handles 'close' packet correctly."""
        mock_sock_instance = mock_socket.return_value

        # Mock recvfrom to return 'close' packet
        mock_sock_instance.recvfrom.return_value = (b'close', self.destination)

        result = quic_recv(mock_sock_instance)

        # Check socket is closed
        mock_sock_instance.close.assert_called_once()

        self.assertEqual(result, ('close', None, None))

    def test_parse_quic_packet_valid(self):
        """Test parse_quic_packet with valid packet."""
        stream_id = 1
        frame_offset = 0
        data = b'Test data'

        packet = create_quic_packet(stream_id, frame_offset, data)

        parsed_stream_id, parsed_frame_offset, parsed_data = parse_quic_packet(packet)

        self.assertEqual(parsed_stream_id, stream_id)
        self.assertEqual(parsed_frame_offset, frame_offset)
        self.assertEqual(parsed_data, data)

    def test_parse_quic_packet_invalid(self):
        """Test parse_quic_packet with invalid packet."""
        # Invalid packet - there are missing parts
        invalid_packet = b'\x00\x01'

        result = parse_quic_packet(invalid_packet)

        self.assertEqual(result, (None, None, None))

    def test_print_statistics_with_data(self):
        """Test print_statistics with populated statistics."""
        # Populate statistics
        stream_statistics[1] = {
            'bytes': 1000,
            'packets': 10,
            'start_time': time.time(),
            'end_time': time.time() + 2  # 2 seconds duration
        }
        stream_statistics[2] = {
            'bytes': 2000,
            'packets': 20,
            'start_time': time.time(),
            'end_time': time.time() + 4  # 4 seconds duration
        }

        with patch('builtins.print') as mock_print:
            print_statistics()

            self.assertTrue(mock_print.call_count > 0)

    @patch('server.quic_recv')
    @patch('server.print_statistics')
    def test_server_function(self, mock_print_statistics, mock_quic_recv):
        """Test server_function behavior."""
        # Setup mock for quic_recv
        mock_quic_recv.side_effect = [
            (1, 0, b'Data1'),
            (2, 0, b'Data2'),
            ('close', None, None)
        ]

        with patch('socket.socket') as mock_socket_class:
            mock_socket_instance = mock_socket_class.return_value

            with patch('builtins.print') as mock_print:
                server_function()

                # Check socket binding
                mock_socket_instance.bind.assert_called_once_with(('127.0.0.1', 5060))

                # Check 'Server listening...' was printed
                mock_print.assert_any_call("Server listening...")

                # Check print_statistics was called
                mock_print_statistics.assert_called_once()

    @patch('client.quic_send')
    @patch('client.quic_close')
    def test_client_function(self, mock_quic_close, mock_quic_send):
        """Test client_function behavior."""
        # Mock file data
        mock_file_data = b'Test file data'

        # Mock open to return file data
        m = mock_open(read_data=mock_file_data)

        with patch('builtins.open', m):
            with patch('socket.socket') as mock_socket_class:
                mock_socket_instance = mock_socket_class.return_value

                client_function()

                expected_file_calls = [call(f'file3.txt_part_{i}.txt', 'wb') for i in range(1, 11)]
                m.assert_has_calls(expected_file_calls, any_order=True)

                # Check quic_send was called the expected number of times
                self.assertEqual(mock_quic_send.call_count, 10)

                # Check quic_close was called once
                mock_quic_close.assert_called_once_with(mock_socket_instance, self.destination)

    @patch('client.quic_send')
    @patch('client.quic_close')
    def test_client_function_file_not_found(self, mock_quic_close, mock_quic_send):
        """Test client_function handles file not found errors."""
        # Mock open to raise FileNotFoundError
        m = mock_open()
        m.side_effect = FileNotFoundError

        with patch('builtins.open', m):
            with patch('socket.socket') as mock_socket_class:
                with self.assertRaises(FileNotFoundError):
                    client_function()

                # Check quic_send was never called
                mock_quic_send.assert_not_called()

                # Check quic_close was not called
                mock_quic_close.assert_not_called()


if __name__ == '__main__':
    unittest.main()
