import socket
import threading
from config import *

class Proxy:
    def __init__(self, proxy_host=MASTER_HOST, proxy_port=PROXY_PORT):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.proxy_host, self.proxy_port))
        self.server.listen(5)

    def handle_client(self, client_socket, slave_address):
        # Connect to slave
        slave_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            slave_socket.connect(slave_address)
            print(f"Connected to slave at {slave_address}")

            while True:
                try:
                    # Forward data from client to slave
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    print(f"Proxy forwarding to slave: {data.decode()}")
                    slave_socket.send(data)

                    # Forward response from slave to client
                    response = slave_socket.recv(4096)
                    if not response:
                        break
                    print(f"Proxy forwarding to master: {response.decode()}")
                    client_socket.send(response)
                except Exception as e:
                    print(f"Error in proxy: {e}")
                    break
        except Exception as e:
            print(f"Failed to connect to slave at {slave_address}: {e}")
            error_msg = f"Error: Could not connect to slave at {slave_address[0]}"
            client_socket.send(error_msg.encode())
        finally:
            client_socket.close()
            slave_socket.close()

    def start(self, slave_host=SLAVE1_HOST, slave_port=SLAVE_PORT):
        print(f"Proxy listening on {self.proxy_host}:{self.proxy_port}")
        print(f"Default slave at {slave_host}:{slave_port}")
        
        try:
            while True:
                client_socket, addr = self.server.accept()
                print(f"Accepted connection from {addr}")
                
                handler = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, (slave_host, slave_port))
                )
                handler.start()
        except KeyboardInterrupt:
            print("Shutting down proxy...")
            self.server.close()

if __name__ == "__main__":
    proxy = Proxy()
    proxy.start()
