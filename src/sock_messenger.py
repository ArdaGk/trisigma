import socket
class Messenger:
    def __init__ (self, addr, port, timeout=10):
        self.addr = addr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        self.sock.connect((addr, port))
        self.sock.settimeout(timeout)

    def send (self, msg):
       self.sock.send(msg.encode())
       resp = self.sock.recv(1024)
       return resp.decode()
