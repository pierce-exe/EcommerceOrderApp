# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19

@author: Harkiran, Pierce, Jenita
"""

#List of imports needed for the code 
import socket 

#The purchaser acts as a client to the OrderDept socket, and as a server to the Supervisor
#Setting up the server socket 
port = 30000                    # Reserve a port for your service.
s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
print(host)
s.bind(('127.0.0.1', port))            # Bind to the port
s.listen(5)                     # Now wait for client connection.
print("Waiting for client to connect")

while True:
    conn, addr = s.accept()     # Establish connection with client.
    print("Accepted connection request from client")
    

    #Connect to the socket of the OrderDept when sending an order
    #Connecting to the OrderDept socket 
    #s = socket.socket()             # Create a socket object
    #port = 60000                    # Reserve a port for your service.
    
    #s.connect(('127.0.0.1', port))

    #Close the socket once the transmission is complete
    #conn.close();