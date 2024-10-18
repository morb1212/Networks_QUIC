import socket
from quic import quic_recv, quic_close, print_statistics


def server_function():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    HOST = '127.0.0.1'
    PORT = 5060
    addr = (HOST, PORT)
    sock.bind(addr)

    print("Server listening...")
    stream_ids = list(range(1, 11))

    run = True
    try:
        while run:
            for stream_id in stream_ids:
                result = quic_recv(sock)
                if result == ('close', None, None):
                    run = False
                    break
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error receiving packet: {e}")

    print_statistics()


if __name__ == '__main__':
    server_function()
