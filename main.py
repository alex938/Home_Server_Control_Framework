import logging
from create_server import server
from control import control
import threading

logging.basicConfig(filename='server.log', filemode='a', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    control_instance = control()
    server_instance = server(999, control_instance)

    server_instance.create_socket()
    server_instance.bind_socket()
    server_instance.start_listening()

    accept_connections_thread = threading.Thread(
        target=server_instance.accept_connections, 
        name="AcceptConnectionsThread"
    )
    accept_connections_thread.daemon = True
    accept_connections_thread.start()

    check_active_connections = threading.Thread(
        target=control_instance.check_life, 
        name="LifeCheckThread"
    )
    check_active_connections.daemon = True
    check_active_connections.start()

    control_menu_thread = threading.Thread(
        target=control_instance.menu, 
        name="MenuThread"
    )
    control_menu_thread.daemon = True
    control_menu_thread.start()
    control_menu_thread.join()

    server_instance.stop_server()

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        logging.error("Error in main: " + str(err))
