import struct
import socket
import random
import time
import threading

# Global dictionaries for packet sizes and statistics
stream_packet_sizes = {}
stream_statistics = {}
data_rates = []
packet_rates = []
num_flows_list = []


def set_stream_packet_size(stream_id):
    if stream_id not in stream_packet_sizes:
        packet_size = random.randint(1000, 2000)
        stream_packet_sizes[stream_id] = packet_size
        stream_statistics[stream_id] = {'bytes': 0, 'packets': 0, 'start_time': None, 'end_time': None}
    return stream_packet_sizes[stream_id]


def create_quic_packet(stream_id, sequence_number, data):
    packet_size = set_stream_packet_size(stream_id)
    data = data[:packet_size]  # Ensure data is within packet size
    packet_format = f'I I H {len(data)}s'
    packet = struct.pack(packet_format, stream_id, sequence_number, len(data), data)
    return packet


def parse_quic_packet(packet):
    header_format = 'I I H'
    header_size = struct.calcsize(header_format)
    try:
        stream_id, frame_offset, payload_length = struct.unpack(header_format, packet[:header_size])
        data_format = f'{payload_length}s'
        data = struct.unpack(data_format, packet[header_size:header_size + payload_length])[0]
        return stream_id, frame_offset, data
    except struct.error as e:
        print(f"Error parsing packet: {e}")
        return None, None, None


def send_packet(sock, destination, stream_id, frame_offset, data_chunk):
    packet = create_quic_packet(stream_id, frame_offset, data_chunk)
    sock.sendto(packet, destination)
    stream_statistics[stream_id]['bytes'] += len(data_chunk)
    stream_statistics[stream_id]['packets'] += 1
    stream_statistics[stream_id]['end_time'] = time.time()
    print(
        f"Sent packet to {destination} with size {len(packet)} bytes for stream {stream_id}, frame offset {frame_offset}")


def quic_send(sock, destination, data, stream_id):
    frame_offset = 0
    packet_size = set_stream_packet_size(stream_id)
    threads = []

    while frame_offset < len(data):
        data_chunk = data[frame_offset:frame_offset + packet_size]
        thread = threading.Thread(target=send_packet, args=(sock, destination, stream_id, frame_offset, data_chunk))
        threads.append(thread)
        thread.start()
        frame_offset += packet_size

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    print(f"Finished sending packets to {destination} for stream {stream_id}")


def quic_recv(sock):
    packet, _ = sock.recvfrom(2048)
    if packet == b"close":
        sock.close()
        return "close", None, None

    stream_id, frame_offset, data = parse_quic_packet(packet)
    if stream_id is None:
        print(f"Received invalid packet: {packet}")
        return

    if stream_id not in stream_statistics:
        stream_statistics[stream_id] = {'bytes': 0, 'packets': 0, 'start_time': None, 'end_time': None}

    if stream_statistics[stream_id]['start_time'] is None:
        stream_statistics[stream_id]['start_time'] = time.time()
    stream_statistics[stream_id]['bytes'] += len(data)
    stream_statistics[stream_id]['packets'] += 1
    stream_statistics[stream_id]['end_time'] = time.time()
    return stream_id, frame_offset, data


def quic_close(sock, destination):
    try:
        sock.sendto(b"close", destination)
        sock.close()
        print("QUIC connection closed")
    except socket.error as e:
        print(f"Socket error: {e}")


def print_statistics():
    with open('statistics.txt', 'w') as file:
        for stream_id, stats in stream_statistics.items():
            total_bytes = stats['bytes']
            total_packets = stats['packets']
            start_time = stats['start_time']
            end_time = stats['end_time']
            duration = end_time - start_time if end_time and start_time else 0
            data_rate = total_bytes / duration if duration > 0 else 0
            packet_rate = total_packets / duration if duration > 0 else 0
            file.write(f"Stream {stream_id}:\n")
            file.write(f"\tTotal bytes: {total_bytes}\n")
            file.write(f"\tTotal packets: {total_packets}\n")
            file.write(f"\tData rate: {data_rate:.2f} bytes/sec\n")
            file.write(f"\tPacket rate: {packet_rate:.2f} packets/sec\n")

        total_bytes = sum(stats['bytes'] for stats in stream_statistics.values())
        total_packets = sum(stats['packets'] for stats in stream_statistics.values())
        total_duration = max((stats['end_time'] - stats['start_time']) for stats in stream_statistics.values() if
                             stats['end_time'] and stats['start_time'])
        total_data_rate = total_bytes / total_duration if total_duration > 0 else 0
        total_packet_rate = total_packets / total_duration if total_duration > 0 else 0

        file.write("Overall statistics:\n")
        file.write(f"\tData rate: {total_data_rate:.2f} bytes/sec\n")
        file.write(f"\tPacket rate: {total_packet_rate:.2f} packets/sec\n")

    print(f"\n")
    for stream_id, stats in stream_statistics.items():
        total_bytes = stats['bytes']
        total_packets = stats['packets']
        start_time = stats['start_time']
        end_time = stats['end_time']
        duration = end_time - start_time if end_time and start_time else 0
        data_rate = total_bytes / duration if duration > 0 else 0
        packet_rate = total_packets / duration if duration > 0 else 0
        print(f"Stream {stream_id}:")
        print(f"\tTotal bytes: {total_bytes}")
        print(f"\tTotal packets: {total_packets}")
        print(f"\tData rate: {data_rate:.2f} bytes/sec")
        print(f"\tPacket rate: {packet_rate:.2f} packets/sec")

    total_bytes = sum(stats['bytes'] for stats in stream_statistics.values())
    total_packets = sum(stats['packets'] for stats in stream_statistics.values())
    total_duration = max((stats['end_time'] - stats['start_time']) for stats in stream_statistics.values() if
                         stats['end_time'] and stats['start_time'])
    total_data_rate = total_bytes / total_duration if total_duration > 0 else 0
    total_packet_rate = total_packets / total_duration if total_duration > 0 else 0

    data_rates.append(total_data_rate)
    packet_rates.append(total_packet_rate)
    num_flows_list.append(len(stream_statistics))

    print("Overall statistics:")
    print(f"\tTotal bytes: {total_bytes}")
    print(f"\tTotal packets: {total_packets}")
    print(f"\tData rate: {total_data_rate:.2f} bytes/sec")
    print(f"\tPacket rate: {total_packet_rate:.2f} packets/sec")