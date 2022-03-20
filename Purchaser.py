# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19

@author: Harkiran, Pierce, Jenita
"""

#List of imports needed for the code 
import socket 
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import time


#Define a function local to the Purchaser that will verify a message based on the timestamp
def timestamp_verify(rectime):
    current_time = time.time() #get current timestamp in seconds
    
    if(current_time - rectime <= 60):
        #If the difference is 60 or less (ie one min has passed since message was sent), message is valid
        return True
    
    elif (current_time - rectime > 60):
        #If the different is greater than 60, (ie more than one minute passed since message was sent), message in invalid
        return False


#Initailize the RSA key
key = RSA.generate(2048)

#Generate private key 
private_key = key.export_key()
priv_key_purch = RSA.importKey(private_key)
priv_key_purch = PKCS1_OAEP.new(priv_key_purch)
    
#Generate public key 
public_key = key.publickey().export_key()
pub_key_purch = RSA.importKey(public_key)
public_key_purch = PKCS1_OAEP.new(pub_key_purch)
    
#Write the public key to the .pem file, accessible by Supervisor and Purchaser
file_out = open("purchaser_public_key.pem", "wb")
file_out.write(public_key)
file_out.close()

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