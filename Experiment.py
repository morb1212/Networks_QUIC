import subprocess
import time
import matplotlib.pyplot as plt

# Define the number of experiments and the range of stream numbers
min_streams = 1
max_streams = 10
results = {'num_streams': [], 'data_rates': [], 'packet_rates': []}


def run_experiment(streams):
    # Update the number of streams in the client script
    with open('client.py', 'r') as file:
        client_script = file.read()
    client_script = client_script.replace(f'Number_Of_Streams = 10', f'Number_Of_Streams = {streams}')
    client_script = client_script.replace(f'Number_Of_Streams = {streams-1}', f'Number_Of_Streams = {streams}')
    with open('client.py', 'w') as file:
        file.write(client_script)

    # Start the server
    server_process = subprocess.Popen(['python3', 'server.py'])

    # Give the server time to start
    time.sleep(2)

    # Run the client
    subprocess.run(['python3', 'client.py'])

    # Give the server time to finish writing statistics
    time.sleep(2)

    # Close the server
    server_process.terminate()

    # Wait for the server process to terminate
    server_process.wait()

    # Collect statistics
    try:
        with open('statistics.txt', 'r') as file:
            lines = file.readlines()

        # # Debug: Print the content of the statistics file
        # print("Content of statistics.txt:")
        # for line in lines:
        #     print(line.strip())

        # Extract the data rates and packet rates from the file
        if len(lines) > 1:
            data_rate_line = lines[-2].split(':')
            packet_rate_line = lines[-1].split(':')

            data_rate = float(data_rate_line[1].strip().split()[0]) if len(data_rate_line) > 1 else 0
            packet_rate = float(packet_rate_line[1].strip().split()[0]) if len(packet_rate_line) > 1 else 0

            results['num_streams'].append(num_streams)
            results['data_rates'].append(data_rate)
            results['packet_rates'].append(packet_rate)
        else:
            print("Statistics file does not contain the expected data.")

    except Exception as e:
        print(f"Error reading statistics: {e}")


if __name__ == '__main__':
    for num_streams in range(1, 11):  # Adjust range as needed
        print(f"----------------------------------\n\nEXPERIMENT Number {num_streams}:\n")
        run_experiment(num_streams)

    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.plot(results['num_streams'], results['data_rates'], marker='o')
    plt.xlabel('Number of Streams')
    plt.ylabel('Data Rate (bytes/sec)')
    plt.title('Data Rate vs Number of Streams')

    plt.subplot(1, 2, 2)
    plt.plot(results['num_streams'], results['packet_rates'], marker='o')
    plt.xlabel('Number of Streams')
    plt.ylabel('Packet Rate (packets/sec)')
    plt.title('Packet Rate vs Number of Streams')

    plt.tight_layout()
    plt.show()
