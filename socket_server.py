import socket


class SocketServer:
    def __init__(self, host='192.168.2.183', port=8082):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f'Server started on {self.host}:{self.port}')
        self.client_socket, addr = self.server_socket.accept()
        print(f'Client connected from {addr}')

    def send_data(self, data):
        self.client_socket.sendall(data.encode())

    def receive_data_until_exit(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if data:
                    print(f'Received data: {data.decode()}')
                    self.send_data("pong")
            except ConnectionResetError:
                print('Client disconnected')
                self.server_socket.listen(1)
                print(f'Server started on {self.host}:{self.port}')
                self.client_socket, addr = self.server_socket.accept()
                print(f'Client connected from {addr}')


if __name__ == '__main__':
    server = SocketServer()
    server.start()
    server.receive_data_until_exit()
