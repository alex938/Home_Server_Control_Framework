import logging
import socket
from control import control

class server():
    def __init__(self, port, control):
        self.ip = self.get_ip()
        self.port = port
        self.socket = None
        self.bind = None
        self.connection_list = []
        self.address_list = []
        self.control = control

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        try:
            s.connect(('10.10.10.10', 1))
            ip = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return ip

    def create_socket(self):
        print("1. Attempting to create socket")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
            print("[+] Socket created sucessfully")
        except socket.error as err:
            logging.error("Error creating socket: " + str(err))
        finally:
            pass

    def bind_socket(self):
        print("2. Attempting to bind socket")
        try:
            self.socket.bind((self.ip, self.port))
            print("[+] IP/PORT bound successfully")    
        except socket.error as err:
            logging.error("Error binding: " + str(err))
        finally:
            pass

    def start_listening(self):
        print("3. Attempting to listen for connections")
        try:
            self.socket.listen(5)
            print("[+] Listening for connections on {}:{}".format(str(self.socket.getsockname()[0]), str(self.socket.getsockname()[1])))    
        except socket.error as err:
            logging.error("Error listening: " + str(err))
        finally:
            pass

    def accept_connections(self):
        try:
            while True:
                conn, address = self.socket.accept()
                print("\n[+] Connection established from: {}:{}".format(str(address[0]), str(address[1])))
                self.control.add_connection(conn, address)
        except socket.error as err:
            logging.error("Error: " + str(err))
        finally:
            pass

    def stop_server(self):
        try:
            print("\nAttempting to close server socket")
            self.socket.close()
            print("Server socket closed successfully")
        except socket.error as err:
            logging.error("Error: " + str(err))
        finally:
            pass