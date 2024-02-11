import os
from log_controller import CreateLogger
from create_server import CreateServer
from server_controller import CreateController
from file_manager import CreateFileManager
import toml

def load_config():
    """
    Loads the toml configuration file.

    Returns:
        dict: Containing the config.toml parameters.

    Raises:
        FileNotFoundError: If there is an SSL error.
        Exception: If there is a socket error.
    """
    try:
        with open('config.toml', 'r') as config_file:
            config = toml.load(config_file)
        return config
    except FileNotFoundError:
        print("config.toml not found, please ensure the config file is accessible")
    except Exception as err:
        print("Error loading config.toml: " + str(err))

def main():
    """
    Main function to load the toml config and create all instances required the server.
    """
    config = load_config()

    server_logger = CreateLogger("server")
    auth_logger = CreateLogger("auth")
    file_manager_instance = CreateFileManager()
    controller_instance = CreateController(server_logger, auth_logger, file_manager_instance)
    server_instance = CreateServer(config['server']['ip'], server_logger, controller_instance)

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print("Error in main: " + str(err))