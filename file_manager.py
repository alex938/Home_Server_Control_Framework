import os
import tqdm
import hashlib
import sys

class CreateFileManager():
    """
    CreateFileManager class for file management on the server. This checks and creates required folder structure
    and populates lists with required information

    Attributes:
        _authorised_ips (list): A list for authorised IPs. IPs taken fron authorised_ips.txt
        _self._last_5_auth_messages (list): A list for the last 5 auth messges taken from auth.log
        _self._files_in_send_folder (list): A list to contain filnames of files in the tool_box folder
        _self._binary_paths (list): To hold a list of paths to directories for the known good hashes list
    """
    def __init__(self):
        self._authorised_ips = []
        self._last_5_auth_messages = []
        self._files_in_send_folder = []
        
        #replace with folders of known good binaries i.e["/bin", "/usr/bin", "/sbin", "/usr/sbin"]
        self._binary_paths = ["/usr/bin"] 

        self.load_authorised_ips()
        self.load_auth_messages()
        self.generate_known_good_hashes()
        self.populate_send_files_folder()
        self.create_downloaded_files_folder()
        self.process_dumps_exists()
        self.sysinfo_dumps_exists()
        self.disk_dumps_exists()

    @staticmethod
    def create_downloaded_files_folder() -> None:
        """
        Creates a 'downloaded_files' folder if one does not exist
        """
        if not os.path.exists("downloaded_files"):
            os.mkdir("downloaded_files")
        
    def load_authorised_ips(self) -> None:
        """
        Reads the authorised_ips.txt file
        """
        self.check_authorised_ips_exists()
        with open("authorised_ips.txt", "r") as ips:
            self._authorised_ips = [line.strip() for line in ips]

    @staticmethod    
    def check_authorised_ips_exists() -> None:
        """
        Creates an 'authorised_ips.txt' file if one does not exist
        """
        if not os.path.exists("authorised_ips.txt"):
            with open("authorised_ips.txt", "w") as file:
                pass
    
    def load_auth_messages(self) -> None:
        """
        Refreshes the authorisation messages for later slicing
        """
        with open("auth.log", "r") as auth_messages:
            self._last_5_auth_messages = [line.strip() for line in auth_messages]
    
    @property       
    def get_authorised_ips(self) -> list:
        """
        Refreshes the authorised IPs list

        Returns:
            list: A list of authorised IPs
        """
        self.load_authorised_ips()
        return self._authorised_ips
    
    @property
    def get_last_5_auth_messages(self) -> list:
        """
        Retrieves the last 5 items from the auth.log

        Returns:
            list: A list containing the last 5 items from the auth.log
        """
        self.load_auth_messages()
        return self._last_5_auth_messages[-5:]

    def get_all_binary_full_paths(self, paths) -> list:
        """
        Creates a list of files and their paths from a specified top level directory

        Args:
            paths (list): The list of the directories specified for hashing

        Returns:
            list: A list of all files for and paths for hashing
        """
        list_of_all_binaries_paths = []
        for path in paths:
            for binary in os.listdir(path):
                full_binary_path = os.path.join(path, binary)
                if os.path.isfile(full_binary_path):
                    list_of_all_binaries_paths.append(full_binary_path)
        return list_of_all_binaries_paths

    def generate_known_good_hashes(self) -> None:
        """
        Creates a known good hashes file containing file name and hash
        """
        binary_paths = self.get_all_binary_full_paths(self._binary_paths)
        with open ("known_good_binary_hashes.txt", "w") as hash_file:
            for binary_path in tqdm.tqdm(binary_paths, desc="Generating known good binary hashes...", 
                                         unit="file", file=sys.stdout):
                hash_value = self.calculate_sha256_of_binary(binary_path)
                if hash_value:
                    hash_file.write("{}:{}".format(binary_path, hash_value))
    
    @staticmethod
    def calculate_sha256_of_binary(file_path) -> str:
        """
        Creates a hash of an input file

        Args:
            file_path (str): The file path of the file to hash

        Returns:
            str: Hex digest of hashed file
        """
        hash_file_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as binary:
                for block in iter(lambda: binary.read(4096), b""):
                    hash_file_sha256.update(block)
            return hash_file_sha256.hexdigest()
        except Exception as err:
                print("Error processing {} due to {}".format(binary, str(err)))
                return None

    def populate_send_files_folder(self) -> None:
        """
        Populates a list with the files in the tool_box folder
        """
        self.send_dir_exists()
        self._files_in_send_folder = os.listdir("./tool_box")
        
    @staticmethod
    def send_dir_exists() -> None:
        """
        Creates a 'tool_box' folder if one does not exist
        """
        if os.path.isdir("./tool_box"): return
        else: os.mkdir("tool_box")

    @staticmethod
    def process_dumps_exists() -> None:
        """
        Creates a 'client_process_dumps' folder if one does not exist
        """
        if os.path.isdir("./client_process_dumps"): return
        else: os.mkdir("client_process_dumps")

    @staticmethod
    def sysinfo_dumps_exists() -> None:
        """
        Creates a 'client_sysinfo_dumps' folder if one does not exist
        """
        if os.path.isdir("./client_sysinfo_dumps"): return
        else: os.mkdir("client_sysinfo_dumps")

    @staticmethod
    def create_downloaded_files_folder() -> None:
        """
        Creates a 'downloaded_files folder if one does not exist
        """
        if os.path.isdir("./downloaded_files"): return
        else: os.mkdir("downloaded_files")

    @staticmethod
    def disk_dumps_exists() -> None:
        """
        Creates a 'client_disk_dumps' folder if one does not exist
        """
        if os.path.isdir("./client_disk_dumps/"): return
        else: os.mkdir("client_disk_dumps")