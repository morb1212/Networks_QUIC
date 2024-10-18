import socket
from quic import quic_send, quic_close
import time
import os

Number_Of_Streams = 10

# this function splits one file into many files
def split_file(file_path, n):
    # Ensure the file exists
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return []

    # Read the entire file content
    with open(file_path, 'rb') as file:
        data = file.read()

    # Calculate the size of each chunk
    file_size = len(data)
    chunk_size = file_size // n

    # Split the data into n parts
    part_files = []
    for i in range(n):
        start_index = i * chunk_size
        end_index = (i + 1) * chunk_size if i < n - 1 else file_size

        # Create a new file for each chunk
        output_file_path = f"{file_path}_part_{i + 1}.txt"
        with open(output_file_path, 'wb') as output_file:
            output_file.write(data[start_index:end_index])

        part_files.append(output_file_path)
        # print(f"Created file: {output_file_path} ({end_index - start_index} bytes)")

    return part_files


def client_function():
    HOST = '127.0.0.1'
    PORT = 5060
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    destination = (HOST, PORT)

    # Split the file into parts for each stream
    file_paths = split_file('file3.txt', Number_Of_Streams)

    for i in range(Number_Of_Streams):
        file_path = file_paths[i]
        with open(file_path, 'rb') as file:
            data = file.read()
            quic_send(sock, destination, data, i+1)

    quic_close(sock, destination)


if __name__ == '__main__':
    client_function()
