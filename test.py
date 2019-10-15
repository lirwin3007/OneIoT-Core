import socket, time, json

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect(("localhost", 1102))
    sock.sendall(bytes("connect_test\ntest", 'ascii'))
    connected = json.loads(str(sock.recv(1024), 'ascii'))

if not connected:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", 1102))
        sock.sendall(bytes("connect\ntest\n192.168.4.2", 'ascii'))
        response = str(sock.recv(1024), 'ascii')
        print("Received: {}".format(response))


while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", 1102))
        sock.sendall(bytes("send_to_device\ntest\nmake_dict\n[]", 'ascii'))
        response = str(sock.recv(1024), 'ascii')
        print("Received: {}".format(response))
