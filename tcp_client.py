#!/usr/bin/python3
import socket

target_host = 'localhost'
target_port = 8080

# create a client socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
client.connect((target_host, target_port))

# send some data
client.send('GET /\r\nHTTP/1.1\r\n\r\n'.encode())

# receive the response
response = client.recv(4096)

print(response)
