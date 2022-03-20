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
priv_key_super = RSA.importKey(private_key)
priv_key_super = PKCS1_OAEP.new(priv_key_super)
    
#Generate public key 
public_key = key.publickey().export_key()
pub_key_super = RSA.importKey(public_key)
public_key_super = PKCS1_OAEP.new(pub_key_super)
    
#Write the public key to the .pem file, accessible by Supervisor and Purchaser
file_out = open("supervisor_public_key.pem", "wb")
file_out.write(public_key)
file_out.close()

#The supervisor is a client to the OrderDept socket and the Purchaser socket

#Connecting to the OrderDept socket 
s_order = socket.socket()             # Create a socket object
port = 60000                    # Reserve a port for your service.

s_order.connect(('127.0.0.1', port))

#Connecting to the Purchaser socket 
s_purch = socket.socket()             # Create a socket object
port = 30000                    # Reserve a port for your service.

s_purch.connect(('127.0.0.1', port))


#Closing the s_order socket 
#s_order.close()

#Closing the s_purch socket
#s_purch.close()