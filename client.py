import socket

TARGET_HOST = '127.0.0.1'
TARGET_PORT = 9998

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((TARGET_HOST, TARGET_PORT))

client.send(b'Hello server')

response = client.recv(4096)

print(response.decode())
client.close()