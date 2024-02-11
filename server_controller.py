import socket
import ssl
import sys
import threading
import time
import os
import datetime
from base64 import b64decode, b64encode
from abc import abstractmethod, ABC
from colorama import init, Back, Fore

init(autoreset=True)

#Future work, monkey patch socket.socket.send to apply EOM delimiter on all server sends.
'''
EOM = '<EOM488965>'
def add_eom_delimiter_to_socket_send(send_without_eom):
    def send_with_eom(self, data):
        return original_send(self, data + EOM.encode())
    return send_with_eom
socket.socket.send = add_eom_delimiter_to_socket_send(socket.socket.send)
'''

class SetupController(ABC):
    def __init__(self, server_logger, auth_logger, file_manager):
        """
        Initialises the attributes of the SetupController class.

        Args:
            server_logger (Logger): An instance of the Logger class used for logging server-related information.
            auth_logger (Logger): An instance of the Logger class used for logging authentication-related information.
            file_manager (FileManager): An instance of the FileManager class used for managing files.

        Attributes:
            _connection_list (list): An empty list to store connection objects.
            _address_list (list): An empty list to store address objects.
            _server_logger (Logger): The provided server_logger object.
            _auth_logger (Logger): The provided auth_logger object.
            _file_manager (FileManager): The provided file_manager object.
            _break_client_control_loop (bool): A flag to control the client control loop.
            _menu_items (dict): A dictionary containing command descriptions for the main menu.
            _control_client_menu_items (dict): A dictionary containing command descriptions for the control client menu.
        """
        self._connection_list = []
        self._address_list = []
        self._server_logger = server_logger
        self._auth_logger = auth_logger
        self._file_manager = file_manager
        self._break_client_control_loop = False
        self._menu_items = {'help':'Display all commands',
                            'r':'Refresh statistics',
                            'list':'List connected clients',
                            'set':'Interact with cient (set ID) i.e. set 1',
                            'good':'Regenerate known good hashes file',
                            'exit':'Shutdown server and send close signal to clients'}
        self._control_client_menu_items = {'help':'Display all commands',
                                        'r':'Refresh statistics',
                                        'kill':'Kill this client connection',
                                        'put':'Send a file to the client',
                                        'get':'Download a file from the client',
                                        'processes':'List processes running on the client',
                                        'sysinfo':'Display client OS version, CPU and memory information',
                                        'disk':'Display client disk useage',
                                        'listdir':'List directory on client',
                                        'exit':'Return to main menu'}

    @abstractmethod
    def socket_for_controller(self):
        """
        Placeholder method for socket_for_controller.
    
        This method is a placeholder in the SetupController class and does not have any implementation.
        It must be overidden.
        """
        pass
    
class CreateController(SetupController):
    def __init__(self, server_logger, auth_logger, file_manager):
        """
        Initialises the CreateController class with the provided loggers and file manager.

        Args:
            server_logger (Logger): The logger for server-related logs.
            auth_logger (Logger): The logger for authentication-related logs.
            file_manager (FileManager): The file manager object.
        """
        super().__init__(server_logger, auth_logger, file_manager)
        self._socket = None
        
        check_alive_thread = threading.Thread(target=self.check_clients_are_alive, args=())
        check_alive_thread.daemon = True
        check_alive_thread.start()

    #The following functions are for connection management

    def socket_for_controller(self, socket):
        """
        Sets the provided socket as the controller's socket and accepts incoming connections.

        Args:
            socket (Socket): The socket to be set as the controller's socket.

        Raises:
            SSLError: If there is an SSL error.
            socket.error: If there is a socket error.
        """
        self._socket = socket
        try:
            while True:
                conn, address = self._socket.accept()
                self.authorise_client(conn, address)
        except (ssl.SSLError, socket.error) as err:
            self._server_logger.logger.error(str(err))
            
    def authorise_client(self, conn, address):
        """
        Checks if the client's IP address is authorized and adds the connection to the controller if it is,
        otherwise logs the rejection.

        Args:
            conn: The connection object.
            address: The IP address and port of the client.

        Raises:
            Exception: If there is an error authorising the client.
        """
        try:
            if address[0] in self._file_manager.get_authorised_ips:
                self.add_authorised_connection_to_controller(conn, address)
            else: 
                self._auth_logger.logger.info("Client connected and rejected: "
                                              "{}:{}".format(address[0], address[1]))
                conn.close()
        except Exception as err:
                self._auth_logger.logger.error("Error authorising client: "
                                    "{}:{}".format(address[0], address[1]))
                
    def add_authorised_connection_to_controller(self, conn, address):
        """
        Adds an authorised connection to the controller.

        Args:
            conn: The connection object representing the client connection.
            address: The address of the client.

        Raises:
            Exception: If there is an error adding the client to the controller.
        """
        try:
            self._connection_list.append(conn) 
            self._address_list.append(address)
            self._auth_logger.logger.info("Client connected and authorised: " 
                                            "{}:{}".format(address[0], address[1]))
        except Exception as err:
            self._auth_logger.logger.error("Error adding authorised client to controller: "
                                            "{}:{}".format(address[0], address[1]))
    
    #The following functions are for main menu management

    def display_menu(self):
        """
        Displays the menu and prompts for user input.
        """
        while True:
            self.display_controller_statistics()   
            cmd = input("\nCommand: ")
            os.system("clear")
            if not self.validate_input(cmd): 
                print(Back.RED + "Command not recognised, type 'help' for command listing")
            
    def validate_input(self, cmd):
        """
        Validates the user input.

        Args:
            cmd (str): The user input command.

        Returns:
            bool: True if the input is valid.
            bool: False if the input is invalid.
        """
        if cmd.split(" ")[0] in self._menu_items.keys(): 
            self.action_input(cmd)
            return True

    def action_input(self, cmd):
        """
        Performs an action based on the user input.

        Args:
            cmd (str): The user input command.
        """
        if cmd == "help": self.display_help()
        elif cmd == "r": pass
        elif cmd == "exit": self.shutdown_controller_and_close_clients()
        elif cmd == "list": self.display_connected_clients
        elif cmd == "good": self._file_manager.generate_known_good_hashes()
        elif cmd.startswith("set"): self.set_session(cmd)

    def display_help(self):
        """
        Displays the available commands and their descriptions.
        """
        for command, description in self._menu_items.items():
            print(Back.GREEN + "{} - {}".format(command, description))
     
    def display_controller_statistics(self):
        """
        Displays the controller statistics.
        """          
        print("\n*** SERVER INFO AND LOGS ***")
        print("Number of connected clients: {}\n\nLast 5 logged auth attempts:\n{}".format(
            self.number_of_connected_clients,
            self.format_last_5_auth_messages))
        print("*" * 28)
    
    @property
    def number_of_connected_clients(self):
        """
        Returns the number of connected clients.

        Returns:
            int: The number of connected clients.
        """
        return len(self._address_list)
    
    @property
    def display_connected_clients(self):
        """
        Displays the list of connected clients.

        Returns:
            list - The formatted list of connected clients if there are any.
            str - "No connected clients" if the list is empty.
        """
        if self.number_of_connected_clients:
            return self.format_list_client_display
        print(Back.RED + "No connected clients")
    
    @property    
    def format_list_client_display(self):
        """
        Formats and displays the list of connected clients.
        """
        print(Back.GREEN + "ID - Client")
        for i, address in enumerate(self._address_list):
            print(Back.GREEN + "{}  - {}".format(i, address[i]))

    @property
    def format_last_5_auth_messages(self):
        """
        Formats and returns the last 5 authentication messages.

        Returns
            str: A string containing the formatted last 5 authentication messages or "None" if there are no messages.
        """
        if not self._file_manager.get_last_5_auth_messages:
            return "None"
        else:
            temp = []
            for _ in self._file_manager.get_last_5_auth_messages:
                temp.append(_.split(' - ')[0] + ' - ' + ' '.join(
                    _.split(" - ")[2].split()))
            return "\n".join(temp)

    #The following functions are used to check clients are alive

    def receive_hello_data_from_clients(self, session_id):
        """
        Receives data from a specific client.

        Parameters:
            session_id (int): The ID of the session for receiving data from clients.

        Returns:
            str: The received data from the client as a string.
        """
        data = ""
        while True:
            chunk = self._connection_list[session_id].recv(1024).decode("utf-8")
            if not chunk: return False
            data += chunk
            if "<EOM488965>" in data: break
        return data.replace("<EOM488965>", "")
      
    def check_clients_are_alive(self):
        """
        Periodically checks if the connected clients are still alive.
        """
        while True:
            time.sleep(10)
            if self._connection_list:
                for i, conn in enumerate(self._connection_list):
                    try:
                        self._connection_list[i].send(str.encode('hello<EOM488965>'))
                        recv_data = self.receive_hello_data_from_clients(i)
                        if not recv_data: raise Exception
                    except Exception as err:
                        self._server_logger.logger.info("Connection closed: {}".format(
                            self._address_list[i][0]))
                        del self._address_list[i]
                        del self._connection_list[i]

    #The following functions close connections with clients and 
    #stop the server when the 'exit' command is called on the main menu

    def shutdown_controller_and_close_clients(self):
        """
        Shuts down the controller and closes all connected clients.

        If there are any connected clients, it iterates over the connection list and sends an exit command to each client,
        closes the connection, and logs the closure.

        Raises:
            Socket exception: If there is an error closing a client connection.
        """
        if self.number_of_connected_clients:
            for i, conn in enumerate(self._connection_list):
                try:
                    self._connection_list[i].send(str.encode('exit<EOM488965>'))
                    time.sleep(1)
                    conn.close()
                    self._server_logger.logger.info("Connection closed due to exit command: {}".format(
                        self._address_list[i][0]))
                except socket.error as err:
                    self._server_logger.logger.error(str(err))
        self.stop_server()
                              
    def stop_server(self):
        """
        Stops the server by closing the server socket and logs the closure.

        Raises:
            ssl.SSLError exception: If there is a SSL error raised it is subsquently logged and the program exits.
        """
        try:
            self._socket.close()
            self._server_logger.logger.info("Server socket closed successfully")
            time.sleep(1)
            sys.exit()
        except ssl.SSLError as err:
            self._server_logger.logger.error(str(err))
            sys.exit()

    #The following functions control individual session interaction from user input

    def set_session(self, user_input):
        """
        Sets a session based on user input.

        It checks if a session exists based on the user input and calls the control_client method with the entered client ID.

        Args:
            user_input (str): The user input to set a session.
        """
        if self.session_exists(user_input):
            self.control_client(self.get_entered_client_id(user_input))

    def session_exists(self, user_input):
        """
        Checks if a session exists based on user input.

        It checks if the entered client ID exists in the range of the address list and returns True if it does.
        Otherwise, it prints an error message.

        Args:
            user_input (str): The user input to check if a session exists.

        Returns:
            bool: True if the session exists, otherwise prints an error message.
        """
        if self.get_entered_client_id(user_input) in range(len(self._address_list)): return True
        else: print(Back.RED + "Client ID does not exist, please enter ID from 'list'")

    def get_entered_client_id(self, user_input):
        """
        Get the entered client ID from user input.

        Args:
            user_input (str): The user input string.

        Returns:
            int: The entered client ID, or None if no client ID was entered.

        Raises:
            ValueError except: Catches a non-int entry, returns the user back to the main menu.
        """
        if self.did_user_enter_a_client_id(user_input):
            try:
                client_id = user_input.split(' ')
                client_id = int(client_id[1])
                return client_id
            except ValueError:
                pass

    def did_user_enter_a_client_id(self, user_input):
        """
        Check if a client ID was entered.

        Args:
            user_input (str): The user input string.

        Returns:
            bool: True if a client ID was entered, False otherwise.
        """
        if user_input != "set": return True

    #The following functions control the client command menu and user input

    def control_client(self, client_id):
        """
        Control the client with the given ID.

        Args:
            client_id (str): The client ID.

        Raises:
            Exception: Used to catch a scenario in which a client disconnects while the user is on the client
            command menu. Alerts the user and clears the screen, breaks the loop and returns back to the main menu.
        """
        print(Back.GREEN + "Connected to client "+ str(self._address_list[client_id][0]))
        self._break_client_control_loop = False
        while True:
            if self._break_client_control_loop:
                break
            try:
                self.display_controller_statistics()
                cmd = input("\nClient " + str(self._address_list[client_id][0] + ": "))
                os.system("clear")
                if not self.validate_control_client_input(cmd):
                    print(Back.RED + "Command not recognised, type 'help' for command listing")
                else: self.action_validated_client_command(cmd, client_id)
            except:
                os.system("clear")
                print(Back.RED + "Client disconnected")
                break

    def validate_control_client_input(self, cmd):
        """
        Validate user input for controlling the client.

        Args:
            cmd (str): The user input command to be validated.

        Returns:
            bool: True if the input command is valid and present in the menu items dictionary, False otherwise.
        """
        if cmd in self._control_client_menu_items.keys(): return True

    def action_validated_client_command(self, cmd, client_id):
        """
        Perform different actions based on the user input command for a specific client.

        Args:
            cmd (str): The user input command.
            client_id (int): The ID of the client.
        """
        if cmd == "help": self.display_help_client_menu()
        elif cmd == "exit": self.break_control_client_loop()
        elif cmd == "kill": self.kill_client_connection(client_id)
        elif cmd == "put": self.start_file_send(client_id)
        elif cmd == "get": self.get_file_name_to_download(client_id)
        elif cmd == "processes": self.get_client_processes(client_id)
        elif cmd == "sysinfo": self.get_client_sysinfo(client_id)
        elif cmd == "disk": self.get_client_disk_info(client_id)
        elif cmd == "listdir": self.get_dir_to_list(client_id)
        else: pass

    def break_control_client_loop(self):
        """
        A function to turn the break client control loop variable to True. This is checked in the while loop
        of the client control command menu.
        """
        self._break_client_control_loop = True

    #The following functions provide client directory listing based on user input

    def get_dir_to_list(self, client_id):
        """
        Requests user to enter directory to list or breaks loop on the exit command.

        Args:
            client_id (str): The ID of the client for which the disk information is requested.
        """
        while True:
            dir_to_list = input("Enter directory to list or 'exit': ")
            if dir_to_list == "exit":
                break
            self.get_dir_listing(client_id, dir_to_list)

    def get_dir_listing(self, client_id, dir_to_list):
        """
        Builds listdir message to send to client and begins the receive functions.

        Args:
            client_id (str): The ID of the client for which the disk information is requested.
            dir_to_list (str): The directory to list.
        """
        construct_data_to_send = "listdir|" + dir_to_list + "<EOM488965>"
        self._connection_list[client_id].send(str.encode(construct_data_to_send))
        self.recv_dir_listing_from_client(client_id)

    def recv_dir_listing_from_client(self, client_id):
        """
        Receives directory listing from the client and displays on screen. Displays 'Nothing received'
        message if no listing is received.

        Args:
            client_id (str): The ID of the client for which the disk information is requested.
        
        Raises:
            Exception: Used to catch an issue when a directory listing is not received. This happens on 
            occassion when a 'hello' message is received from the alive check.
        """
        try:
            recv_data = self.receive_data_from_clients(client_id)
            if recv_data.startswith("dirlisting|"):
                dir_listing = recv_data.split("|")[1]
                print(dir_listing)
        except:
            print(Back.RED + "Nothing received, please try again")

    #The following functions provide disk information request and receive functionality

    def get_client_disk_info(self, client_id):
        """
        Builds disk message to send to client and begins the receive functions.

        Args:
            client_id (str): The ID of the client for which the disk information is requested.
        """
        construct_data_to_send = "disk<EOM488965>".format(str(client_id))
        self._connection_list[client_id].send(str.encode(construct_data_to_send))
        self.recv_disk_information_from_client(client_id)

    def recv_disk_information_from_client(self, client_id):
        """
        Receives disk information from the client and displays on screen as well as saving to file. 

        Args:
            client_id (str): The ID of the client for which the disk information is requested.

        Raises:
            IOError exception: To catch an issue writing the file to disk and write to server log.
            Exception: Used to catch all other cases and write to server log.
        """
        try:
            recv_data = self.receive_data_from_clients(client_id)
            full_filename = self.build_filename(self._address_list[client_id][0], "disk")
            with open(f"./client_disk_dumps/{full_filename}", "w") as file:
                file.write(recv_data.split("|")[1])
            print(Back.GREEN + "Disk information dump saved to ./client_disk_dumps/{}".format(full_filename))
            self._server_logger.logger.info("Disk information dump of client {} saved to {}".format(
                self._address_list[client_id][0], full_filename))
            print("\n" + Back.GREEN + recv_data.split("|")[1])
        except IOError as err:
            self._server_logger.logger.error("Error writing disk dump {}".format(str(err)))
        except Exception as err:
            self._server_logger.logger.error("Error writing disk dump {}".format(str(err))) 
            pass

    #The following functions provide sysinfo information request and receive functionality

    def get_client_sysinfo(self, client_id):
        """
        Builds sysinfo message to send to client and begins the receive functions.

        Args:
            client_id (str): The ID of the client for which the sysinfo information is requested.
        """
        construct_data_to_send = "sysinfo<EOM488965>".format(str(client_id))
        self._connection_list[client_id].send(str.encode(construct_data_to_send))  
        self.recv_sysinfo_from_client(client_id)   

    def recv_sysinfo_from_client(self, client_id):
        """
        Receives sysinfo information from the client and displays on screen as well as saving to file. 

        Args:
            client_id (str): The ID of the client for which the sysinfo information is requested.
        """
        try:
            recv_data = self.receive_data_from_clients(client_id)
            full_filename = self.build_filename(self._address_list[client_id][0], "sysinfo")
            with open(f"./client_sysinfo_dumps/{full_filename}", "w") as file:
                file.write(recv_data.split("|")[1])
            print(Back.GREEN + "Sysinfo dump saved to ./client_sysinfo_dumps/{}".format(full_filename))
            self._server_logger.logger.info("Sysinfo dump of client {} saved to {}".format(
                self._address_list[client_id][0], full_filename))
            print("\n" + Back.GREEN + recv_data.split("|")[1])
        except IOError as err:
            self._server_logger.logger.error("Error writing process dump {}".format(str(err)))
        except Exception as err:
            self._server_logger.logger.error("Error writing process dump {}".format(str(err))) 
            pass

    #The following functions provide process information request and receive functionality

    def get_client_processes(self, client_id):
        """
        Builds process message to send to client and begins the receive functions.

        Args:
            client_id (str): The ID of the client for which the process information is requested.
        """
        construct_data_to_send = "processes<EOM488965>".format(str(client_id))
        self._connection_list[client_id].send(str.encode(construct_data_to_send))
        self.recv_proccess_list_from_client(client_id)

    def recv_proccess_list_from_client(self, client_id):
        """
        Receives process information from the client and saves to file. 

        Args:
            client_id (str): The ID of the client for which the process information is requested.
        """
        try:
            recv_data = self.receive_data_from_clients(client_id)
            full_filename = self.build_filename(self._address_list[client_id][0], "processes")
            with open(f"./client_process_dumps/{full_filename}", "w") as file:
                file.write(recv_data.split("|")[1])
            print(Back.GREEN + "Process dump saved to ./client_process_dumps/{}".format(full_filename))
            self._server_logger.logger.info("Process dump of client {} saved to {}".format(
                self._address_list[client_id][0], full_filename))
            time.sleep(3)
        except IOError as err:
            self._server_logger.logger.error("Error writing process dump {}".format(str(err)))
        except Exception as err:
            self._server_logger.logger.error("Error writing process dump {}".format(str(err))) 
            pass

    #Function to build a filename used to save files

    @staticmethod
    def build_filename(client_id, action_type):
        """
        Function used to build a filename. 

        Args:
            client_id (str): The ID of the client for the filename.
            action_type (str): The command used which will be attached to the filename.

        Returns:
            current_date_time_formatted (str): A filename including the date, cient IP address and action
        """
        current_time = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
        current_date_time_formatted = current_time+"_"+str(client_id)+"_"+action_type
        return current_date_time_formatted

    #A reusable function to receive data from commands and strip the EOM delimiter

    def receive_data_from_clients(self, client_id):
        """
        Function to remove the EOM delimiter from messages received from commands. 
        This is separate to the function used by the check alive messages. 

        Args:
            client_id (str): The ID of the client for which the receive is associated with.

        Returns:
            current_date_time_formatted (str): A filename including the date, cient IP address and action
        """
        data = ""
        while True:
            chunk = self._connection_list[client_id].recv(1024).decode()
            if not chunk: False
            data += chunk
            if "<EOM488965>" in data: break
        return data.replace("<EOM488965>", "")

    #A function to display the client control menu

    def display_help_client_menu(self):
        """
        Used to display the help of the client control menu printing available commands to the screen. 
        """
        for command, description in self._control_client_menu_items.items():
            print(Back.GREEN + "{} - {}".format(command, description))

    #A function to kill the connection of the currently connected client only

    def kill_client_connection(self, client_id):
        """
        Closes client connection on exit command.

        Args:
            client_id (str): The ID of the client for which to send the 'exit' message.
        """
        try:
            self._connection_list[client_id].send(str.encode('exit<EOM488965>'))
            time.sleep(1)
            self._connection_list[client_id].close()
            self._server_logger.logger.info("Server terminated connection,"
                                             "with {}:{}".format(self._address_list[client_id][0], self._address_list[client_id][1]))
            del self._address_list[client_id]
            del self._connection_list[client_id]
            self.break_control_client_loop()
        except:
            self._server_logger.logger.info("Error terminating connection," 
                                            "with {}:{}".format(self._address_list[client_id][0], self._address_list[client_id][1]))

    #The follow functions are used to put a file on the the client

    def start_file_send(self, client_id):
        """
        Calls the file_manager function - populate_send_file_folder which refreshes the files available to send from the 'tool_box' folder.
        Displays the files available to send.

        Args:
            client_id (str): The ID of the client.
        """
        self._file_manager.populate_send_files_folder()
        self.display_files_available_to_send(client_id)

    def display_files_available_to_send(self, client_id):
        """
        Checks there are files in the 'tool_box' folder and prints to the screen. If not, tells the user no
        files are available i.e. no files in the 'tool_box' folder.

        Args:
            client_id (int): The ID of the client.
        """
        if len(self._file_manager._files_in_send_folder) == 0:
            print(Back.RED + "No files available, please put files in 'tool_box' folder\n")
            time.sleep(2)
        else:
            print("ID   Filename")
            for id, file in enumerate(self._file_manager._files_in_send_folder):
                print("{}    {}".format(id, file))
            file_id = int(input("\nEnter file ID to send: "))
            if self.check_file_id_exists(file_id):
                self.send_file_to_client(client_id, self._file_manager._files_in_send_folder[file_id])

    def check_file_id_exists(self, file_id):
        """
        Checks if the user input a correct file ID.

        Args:
            file_id (str): The ID of the file to send.
        """
        if int(file_id) < len(self._file_manager._files_in_send_folder): 
            return True
        else: 
            print(Back.RED + "\nFile ID does not exist")
            time.sleep(2)
    
    def send_file_to_client(self, client_id, file_path_to_send):
        """
        Final step in the send file chain to send the selected file to the client.

        Args:
            file_id (str): The ID of the file to send.
            file_path_to_send (str): Full filepath of file to send retrieved by the file_manager
        """
        try:
            with open(f"./tool_box/{file_path_to_send}", 'rb') as file_to_send:
                file_name = os.path.basename(file_path_to_send).encode()
                fileb64 = b64encode(file_to_send.read())                                     
                construct_data_to_send = b"sendfile|" + file_name + b"|" + fileb64 + b"<EOM488965>"
                self._connection_list[client_id].send(construct_data_to_send)
                self._server_logger.logger.info("File {} transferred to {}".format(
                    file_path_to_send, self._address_list[client_id][0]))
                time.sleep(2)
                print(Back.GREEN + "File sent successfully")
                time.sleep(2)
                os.system("clear")
        except Exception as err:
            self._server_logger.logger.info("Error sending file {} to client {}".format(
                file_path_to_send, self._address_list[client_id][0]))
            self._server_logger.logger.info(str(err))
            print(Back.RED + "Error: file not sent. Please check sever.log")

    #The following functions are used to get a file from the client

    def get_file_name_to_download(self, client_id):
        """
        Request a file path to download from the user.

        Args:
            client_id (str): The ID of the file to send.
        """
        while True:
            file_path_to_download = input("Enter file and path to download: ")
            if file_path_to_download == "exit":
                break
            self.check_download_path_exists(client_id, file_path_to_download)

    def check_download_path_exists(self, client_id, file_path_to_download):
        """
        Check with the client that the requested file exists on the client.

        Args:
            client_id (str): The ID of the file to send.
            file_path_to_download (str): The full file path of the file to get from the client.
        """
        construct_data_to_send = "checkfile|" + file_path_to_download + "<EOM488965>"
        self._connection_list[client_id].send(str.encode(construct_data_to_send))
        if self.recv_file_check_from_client(client_id):
            print(Back.GREEN + "File exists on client")
            self.request_file_from_client(client_id, file_path_to_download)
        else:
            print(Back.RED + "Permission denied or file does not exist on client,"
                  "please try again or 'exit'")

    def recv_file_check_from_client(self, client_id):
        """
        Receive the check file exists message from the client. The client will send 1 if it exists or 0 if
        it does not (or permission denied).

        Args:
            client_id (str): The ID of the file to send.
        """
        recv_data = self.receive_data_from_clients(client_id)
        if recv_data.split("|")[1] == "1":
            return True
        else: return False

    def request_file_from_client(self, client_id, file_path_to_download):
        """
        Receive the file from the client after checks. Client will base64 encode, so function will
        encode back to bytes and base64 decode to handle special characters in original binary encoding.

        Args:
            client_id (str): The ID of the file to send.
            file_path_to_download (str): The full file path of the file to get from the client
        """
        print(Back.YELLOW + "Requesting {} from client".format(file_path_to_download))
        try:
            construct_data_to_send = "request|" + file_path_to_download + "<EOM488965>"
            self._connection_list[client_id].send(str.encode(construct_data_to_send))
            time.sleep(1)
            recv_data = self.receive_data_from_clients(client_id)
            if recv_data.startswith("send|"):
                recv_data = recv_data.split("|")[1]
                recv_data = recv_data.encode()
                recv_data = b64decode(recv_data)
                with open(f"./downloaded_files/{os.path.basename(file_path_to_download)}", "wb") as file:
                    file.write(recv_data)
                    if os.path.exists(f"./downloaded_files/{os.path.basename(file_path_to_download)}"):
                        print(Back.GREEN + "File received and saved {}".format(
                            f"./downloaded_files/{os.path.basename(file_path_to_download)}"))
                    else:
                        print(Back.RED + "Failed to download, please try again")
        except Exception as err:
            print(Back.RED + "Error downloading file")
            print(str(err))
