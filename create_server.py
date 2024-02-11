import socket
import sys
import ssl
import os
import subprocess
import threading
from abc import abstractmethod, ABC
from server_controller import CreateController, SetupController

class ServerSetup(ABC):
    def __init__(self, ip):
        self._server_ip = ip
        self._server_port = 999
        self._socket = None
    
    @abstractmethod
    def create_socket(self):
        """
        Creates a socket object for the server.

        :return: None
        """
        pass
    
    @abstractmethod
    def wrap_socket_tls(self):
        pass
    
    @abstractmethod
    def bind_socket_to_ip_port(self):
        pass

    @abstractmethod
    def start_listening(self):
        pass

    @abstractmethod
    def pass_socket_to_controller(self):
        pass
    
class CertificateSetup(ABC):
    def __init__(self):
        self._certificate = "cert.pem"
        self._key = "key.pem"

        self._certificate_parameters = {
            'format':'x509',
            'rsa_strength':'4096',
            'key_out':'key.pem',
            'cert_out':'cert.pem',
            'common_name':'localhost',
            'expiry_days':'365',
            }
        
        self._cmd = ("openssl req -{} -newkey rsa:{} -keyout {}"
                    " -out {} -days {} -nodes -subj \"/CN={}\"".format(
                        self._certificate_parameters['format'],
                        self._certificate_parameters['rsa_strength'],
                        self._certificate_parameters['key_out'],
                        self._certificate_parameters['cert_out'],
                        self._certificate_parameters['expiry_days'],
                        self._certificate_parameters['common_name']))
               
    @abstractmethod
    def create_certificates(self):
        pass
    
    @abstractmethod
    def does_certificate_exist(self):
        pass
    
class CreateServer(ServerSetup, CertificateSetup):
    def __init__(self, ip, server_logger, controller_instance):
        """
        Initialises the CreateServer object by setting the server IP, server logger, and controller instance.
        It calls several methods to create certificates, create a socket, enable TLS, bind the socket to an IP and port,
        start listening for connections, and ultimately pass the socket to the controller.
    
        Args:
            ip (str): The IP address for the server
            server_logger (object): An instance of the CreateLogger class for logging server events.
            controller_instance (object): An instance of CreateController class for handling client functionality.
        """
        ServerSetup.__init__(self, ip)
        CertificateSetup.__init__(self)
        self._server_logger = server_logger
        self._controller_instance = controller_instance
        self.create_certificates()
        self.create_socket()
        self.wrap_socket_tls()
        self.bind_socket_to_ip_port()
        self.start_listening()
        self.pass_socket_to_controller()
        
    def create_certificates(self):
        """
        Create SSL/TLS certificates if they do not already exist.
        """
        if not self.does_certificate_exist:
            subprocess.run(self._cmd, shell=True)
            self._server_logger.logger.info("New Certificates Created")
            
    @property
    def does_certificate_exist(self) -> bool:
        """
        Checks if the TLS certificates already exist on the server.

        Returns:
            bool: Returns True if the certificate and key files exist, otherwise returns False.
        """
        return os.path.exists(self._certificate) and os.path.exists(self._key)
        
    def create_socket(self) -> None:
        """
        Creates a socket object for the server.

        Raises:
            socket.error: If there is a socket error.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, 
                                        socket.SOCK_STREAM,
                                        proto=socket.IPPROTO_TCP)
            self._server_logger.logger.info("Socket Created")
        except socket.error as err:
            self._server_logger.logger.error(str(err))
            sys.exit()
                        
    def wrap_socket_tls(self):
        """
        Enables TLS for the server by creating a TLS context, loading the server's 
        certificate and key, and wrapping the socket with the TLS context.

        Raises:
            SSLError: If there is a SSL error.
        """
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=self._certificate,
                                    keyfile=self._key)
            self._socket = context.wrap_socket(self._socket, 
                                               server_side=True,
                                               do_handshake_on_connect=False
                                               )
            self._server_logger.logger.info("TLS enabled")
        except ssl.SSLError as err:
            self._server_logger.logger.error(str(err))
            sys.exit()
    
    def bind_socket_to_ip_port(self):
        """
        Binds the server socket to the provided IP address and port.

        Raises:
            socket.error: If there is a socket error.
        """
        try:
            self._socket.bind((self._server_ip, self._server_port))
            self._server_logger.logger.info("Socket bound to: {}:{}".format(
                                            str(self._server_ip),
                                            str(self._server_port)))
        except socket.error as err:
            self._server_logger.logger.error(str(err))
            sys.exit()
              
    def start_listening(self):
        """
        Sets the socket to listen for incoming connections and logs a message 
        indicating that the socket is listening.

        Raises:
            SSLError: If there is a SSL error.
        """
        try:
            self._socket.listen(5)
            self._server_logger.logger.info("Socket listening for connections")
        except (ssl.SSLError, socket.error) as err:
            self._server_logger.logger.error(str(err))
            sys.exit()        

    def pass_socket_to_controller(self):
        """
        Creates a new thread to handle client connections and passes the socket 
        to the controller instance.

        Raises:
            SSLError: If there is an SSL error.
        """
        try:
            handle_client_thread = threading.Thread(
                target=self._controller_instance.socket_for_controller, 
                args=(self._socket,), name="ThreadToHandleClients")
            handle_client_thread.daemon = True
            handle_client_thread.start()
        except (ssl.SSLError, socket.error) as err:
            self._server_logger.logger.error(str(err))
        self._controller_instance.display_menu()