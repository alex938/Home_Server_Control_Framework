import logging
import sys
import time

class control():
    def __init__(self):
        self.connection_list = []
        self.address_list = []
        self.menu_items = ["help - Display commands", 
                            "list - List all established connections", 
                            "set X - Interact with established sessions i.e. set 1"]
        self.command_items = ["help - Display commands", 
                            "uptime - Request client uptime",] 

    def add_connection(self, conn, address):
        self.connection_list.append(conn)
        self.address_list.append(address)

    def menu(self):
        while True:
            cmd = input('Main Menu: ')
            if cmd == 'help':
                [print(i) for i in self.menu_items]
            elif cmd == 'list':
                self.display_connections()
            elif cmd == 'exit':
                self.close_connections()
                sys.exit()
            elif cmd.startswith('set'):
                try:
                    _, session_id = cmd.split(' ')
                    session_id = int(session_id)
                    if session_id in range(len(self.address_list)):
                        print("Attempting to interact with session: {}".format(session_id))
                        self.interact_with_session(session_id) 
                    else:
                        raise ValueError("Invalid session index. Please provide a valid session.")
                except ValueError:
                    print("Invalid session index. Please provide a valid session.")       
            else:
                print("Command not recognised")

    def display_connections(self):
        if len(self.connection_list) > 0:
            for i, conn in enumerate(self.connection_list):
                print("{}. {}:{}".format(str(i), self.get_client_ip_port(conn)[0], self.get_client_ip_port(conn)[1]))
        else:
            print("No established connections")
    
    def close_connections(self):
        if self.connection_list:
            for i, conn in enumerate(self.connection_list):
                try:
                    self.connection_list[i].send(str.encode('exit'))
                    print("Connection closed with: {}:{}".format(self.get_client_ip_port(conn)[0], self.get_client_ip_port(conn)[1]))
                    conn.close()           
                except Exception as err:
                    logging.error("Error closing connection: " + str(err))
    
    @staticmethod
    def get_client_ip_port(conn):
        client_ip_port = conn.getpeername()
        return client_ip_port[0], client_ip_port[1]

    def check_life(self):
        while True:
            time.sleep(5)
            if self.connection_list:
                for i, conn in enumerate(self.connection_list):
                    try:
                        self.connection_list[i].send(str.encode(' '))
                        self.connection_list[i].recv(20480)
                    except:
                        print("\nConnection closed: {}".format(self.address_list[i][0]))
                        del self.connection_list[i]
                        del self.address_list[i]
    
    def interact_with_session(self, session_id):
        print("Connected to client: " + self.address_list[session_id][0])
        while True:
            try:
                cmd = input("Client " + self.address_list[session_id][0] + ": ")
                if cmd == 'help':
                    [print(i) for i in self.command_items]
                elif cmd == 'exit':
                    break
                elif cmd == 'uptime':
                    self.connection_list[session_id].send(str.encode(cmd))
                    recv_data = self.connection_list[session_id].recv(1024)
                    print(str(recv_data.decode("utf-8")))
            except Exception as err:
                logging.error("Error sending commend: " + str(err))
                break
