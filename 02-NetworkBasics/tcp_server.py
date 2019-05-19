import socket
import threading

bind_ip = '0.0.0.0'
bind_port = 7890

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.listen(5)

print('[*] Listening on {ip}:{port}'.format(
    ip=bind_ip,
    port=bind_port))


def handle_client(client_socket):
    # Print out what client sends
    request = client_socket.recv(1024)
    print('[*] Received: {req}'.format(req=request))

    # Send back a packet
    client_socket.send(b'ACK!')
    client_socket.close()


while True:
    client, addr = server.accept()
    print('[*] Accepted connection from: {ip}:{port}'.format(
        ip=addr[0],
        port=addr[1]))

    # Spin up our client thread to handle incoming data
    client_handler = threading.Thread(target=handle_client, args=(client,))
    client_handler.start()

