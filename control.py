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
        print("\nWelcome to the Main Menu. Type 'help' to see available commands.\n")
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
                        print("Invalid session index. Please provide a valid session.")
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
                    self.connection_list[i].send(str.encode('exit<EOM488965>'))
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
                        self.connection_list[i].send(str.encode('alive<EOM488965>'))
                        recv_data = self.receive_from_session(i)
                        if not recv_data:
                            raise Exception()
                    except Exception as err:
                        print(err)
                        print("\nConnection closed: {}".format(self.address_list[i][0]))
                        del self.connection_list[i]
                        del self.address_list[i]
    
    def receive_from_session(self, session_id):
        data = ""
        while True:
            chunk = self.connection_list[session_id].recv(1024).decode("utf-8")
            if chunk == "":
                return False
            data += chunk
            if "<EOM488965>" in data:
                break
        return data.replace("<EOM488965>", "")

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
                    self.connection_list[session_id].send(str.encode(cmd + "<EOM488965>"))
                    recv_data = self.receive_from_session(session_id)
                    print(recv_data)
                else:
                    print("Command not recognised.")
            except Exception as err:
                logging.error("Error sending commend: " + str(err))
                break