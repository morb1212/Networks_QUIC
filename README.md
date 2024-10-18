# EXPERIMENT README

## Overview

This project conducts experiments to analyze data transmission rates using QUIC (Quick UDP Internet Connections) protocol. It consists of a server and client implementation that communicate over UDP, allowing the client to send data in multiple streams. The results are collected and visualized using Matplotlib.

## Project Structure

- **client.py**: Client-side code responsible for splitting a file into chunks and sending it to the server using QUIC.
- **server.py**: Server-side code that receives packets from the client and computes statistics.
- **quic.py**: Contains functions related to QUIC packet creation, sending, and receiving.
- **experiment.py**: Runs the experiment, modifies the client configuration for different stream numbers, and collects statistics for analysis.
- **statistics.txt**: Output file containing data and packet rate statistics from the experiments.

## Requirements

To run this project, ensure you have the following installed:

- Python 3.x
- Matplotlib (`pip install matplotlib`)

## Running the Experiment

1. **Prepare Your Environment**:
   - Place a file named `file3.txt` in the same directory. This file will be split and sent during the experiment.

2. **Run the Server**:
   Open a terminal and run the server:
   ```bash
   python3 server.py
