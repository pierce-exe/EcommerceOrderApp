# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 

@author: Harkiran, Pierce, Jenita
"""
#List of imports needed for the code 
import socket 

#The order department acts as a server, the purchaser and supervisor both connect to the socket 
port = 60000                    # Reserve a port for your service.
s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
print(host)
s.bind(('127.0.0.1', port))            # Bind to the port
s.listen(5)                     # Now wait for client connection.
print("Waiting for client to connect")

while True:
    conn, addr = s.accept()     # Establish connection with client.
    print("Accepted connection request from client")
    
    
    #Close the socket once the transmission is complete
    #conn.close();