import socket
import ssl
import sys
import os
import shutil
from base64 import b64encode, b64decode

class Client():
    """
    Client class for interacting with the server

    Attributes:
        _server_ip (str): The IP address of the server to connect to
        _server_port (str): The port of the server to connect to
        _socket (socket): The socket used for communication
    """
    def __init__(self):
        """
        Initialises a new client instance
        """ 
        self._server_ip = None
        self._server_port = None
        self._socket = None

    def get_ip_port_of_server_from_user(self) -> None:
        """
        Prompt the user enter the IP address of the server to connect to
        """
        while True:
            self._server_ip = input("Enter server IP: ")
            self._server_port = input("Enter server port: ")
            if self.validate_ip_port(self._server_ip, self._server_port):
                break
            print("Please enter a valid IP and PORT.\n")
          
    @staticmethod
    def validate_ip_port(ip, port) -> bool:
        """
        Validate the IP address and port entered

        Args:
            ip (str): The IP address that needs validating
            port (str): The port number that needs validating

        Returns:
            bool: True if both the IP address and port are valid, else returns False
        """
        try:
            socket.inet_pton(socket.AF_INET, ip)
            port = int(port)
            if 1 <= port <= 65535:
                return True
        except (socket.error, ValueError):
            pass
        return False
       
    def create_client_socket(self) -> None:
        """
        Create a client socket
        """
        self._socket = socket.socket(socket.AF_INET, 
                                    socket.SOCK_STREAM,
                                    proto=socket.IPPROTO_TCP)
        
    def wrap_socket_tls(self) -> None:
        """
        Wrap the client socket with TLS
        """
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self._socket = context.wrap_socket(self._socket, 
                                           server_hostname=self._server_ip)
        
    def connect_to_server(self) -> None:
        """
        Connect to the server
        """
        self._socket.connect((self._server_ip, int(self._server_port)))

    def receive_data(self, stream) -> str:
        """
        Used to receive data from the server and strip the EOM delimiter.

        Args:
            stream (socket): The socket stream to receive data from

        Returns:
            str: The received, decoded data.
        """
        data = ""
        while True:
            chunk = stream.recv(1024).decode()
            data += chunk
            if "<EOM488965>" in data:
                break
        return data.replace("<EOM488965>", "")
    
    @staticmethod
    def get_running_processes() -> list:
        """
        Gets a list of running processes via proc directories

        Returns:
            list: A list of running processes
        """
        process_list = []
        for i in os.listdir("/proc"):
            if i.isdigit():
                with open(f"/proc/{i}/comm", 'r') as comm:
                    process_name = comm.readline().strip()
                process_list.append("PID: {}, Name: {}".format(i, process_name))
        return process_list
    
    @staticmethod
    def get_cpu_info() -> str:
        """
        Gets the CPU information

        Returns:
            str: CPU information as a joined string
        """
        cpu = []
        with open('/proc/cpuinfo', 'r') as info:
            for i in info:
                i = i.strip()
                if i.startswith("model name"):
                    cpu.append("Model Name: " + i.split(':', 1)[1].strip())
                if i.startswith("cpu cores"):
                    cpu.append("Cores: " + i.split(':', 1)[1].strip())
                if i.startswith("cpu MHz"):
                    cpu.append("Mhz: " + i.split(':', 1)[1].strip())
        return "\n".join(cpu)

    @staticmethod
    def get_memory_info() -> str:
        """
        Gets the memory information

        Returns:
            str: Memory information as a join string
        """
        memory = []
        with open('/proc/meminfo', 'r') as info:
            for i in info:
                if i.startswith('MemTotal'):
                    memory.append(i.strip())
                elif i.startswith('MemFree'):
                    memory.append(i.strip())
                elif i.startswith('MemAvailable'):
                    memory.append(i.strip())
        return "\n".join(memory)

    def get_os_info(self) -> str:
        """
        Gets OS information

        Returns:
            str: OS information as a joined string
        """
        os_info = []
        with open('/etc/os-release', 'r') as info:
            for i in info:
                if i.startswith('PRETTY_NAME='):
                    os_info.append(i.split('=', 1)[1].strip())
                elif i.startswith('VERSION='):
                    os_info.append(i.split('=', 1)[1].strip())
        return "\n".join(os_info)
    
    def get_disk_info(self) -> str:
        """
        Gets disk information

        Returns:
            str: Disk useage and capacity as a joined string
        """
        total, used, free = shutil.disk_usage("/")
        total_formatted = "Total disk: {:.2f} GB".format(total / (1024**3))
        used_formatted = "Used disk: {:.2f} GB".format(used / (1024**3))
        free_formatted = "Free disk: {:.2f} GB".format(free / (1024**3))
        return total_formatted + "\n" + used_formatted + "\n" + free_formatted

    def ready_to_receive(self):
        """
        This is the main loop to recieve and process server commands
        """
        while True:
            data = self.receive_data(self._socket)

            if data == "hello":
                self._socket.send(str.encode("hello<EOM488965>"))
                
            if data == "exit":
                self._socket.close()
                sys.exit()

            if data == "processes":
                _ = "\n".join(self.get_running_processes())
                prepared_message = "processes|" + _ + "<EOM488965>"
                self._socket.send(str.encode(prepared_message))

            if data == "sysinfo":
                os_ = self.get_os_info()
                cpu = self.get_cpu_info()
                memory = self.get_memory_info()
                prepared_message = ("sysinfo| " + os_ + "\n" + cpu + "\n" + memory + "<EOM488965>")
                self._socket.send(str.encode(prepared_message))       
                
            if data.startswith("sendfile|"):
                try:
                    _, file_name, file_data = data.split("|", 2)
                    file_data = file_data.encode()
                    file_data = b64decode(file_data)
                    with open(file_name, "wb") as file:
                        file.write(file_data)
                        print("File recieved and saved {}".format(file_name))
                except Exception as err:
                    prepared_message = "send|denied<EOM488965>"
                    self._socket.send(prepared_message.encode()) 

            if data.startswith("checkfile|"):
                path_to_check = data.split("|")[1]
                if os.path.isfile(path_to_check) and os.access(path_to_check, os.R_OK):
                    print("Server requested file {}".format(path_to_check))
                    self._socket.send(str.encode("checkfile|1<EOM488965>"))
                else:
                    print("Server requested file {} but it doesn't exist".format(path_to_check))
                    self._socket.send(str.encode("checkfile|0<EOM488965>"))
    
            if data.startswith("request|"):
                try:
                    file_requested = data.split("|")[1]
                    with open(f"{file_requested}", 'rb') as file_to_send:
                        fileb64 = b64encode(file_to_send.read())
                        self._socket.send((b"send|" + fileb64 + b"<EOM488965>"))
                        print("File sent to server: {}".format(file_requested))
                except Exception as err:
                    print("Error sending file: {}".format(str(err)))

            if data == "disk":
                try:
                    disk_info = self.get_disk_info()
                    prepared_message = "diskinfo| " + disk_info + "<EOM488965>"
                    self._socket.send(prepared_message.encode()) 
                except Exception as err:
                    print(str(err))

            if data.startswith("listdir|"):
                dir_to_list = data.split("|")[1]
                try:
                    dir_listing = "\n".join(os.listdir(dir_to_list))
                    prepared_message = "dirlisting| " + dir_listing + "<EOM488965>"
                    self._socket.send(prepared_message.encode()) 
                except FileNotFoundError:
                    dir_listing = "Directory not found"
                    prepared_message = "dirlisting| " + dir_listing + "<EOM488965>"
                    self._socket.send(prepared_message.encode())
                except PermissionError:
                    dir_listing = "Permission denied"
                    prepared_message = "dirlisting| " + dir_listing + "<EOM488965>"
                    self._socket.send(prepared_message.encode()) 
                except NotADirectoryError:
                    dir_listing = "Not a directory"
                    prepared_message = "dirlisting| " + dir_listing + "<EOM488965>"
                    self._socket.send(prepared_message.encode()) 

def main():
    """
    The main entry point for the client that instantiates the Client class.
    """
    try: 
        client_instance = Client()
        client_instance.get_ip_port_of_server_from_user()
        client_instance.create_client_socket()
        client_instance.wrap_socket_tls()
        client_instance.connect_to_server()
        client_instance.ready_to_receive()
    except Exception as err:
        print("Error connecting")
        print(str(err))

if __name__ == '__main__':
    try: 
        main()
    except Exception as err:
        print("Error in main: " + str(err))
        sys.exit()