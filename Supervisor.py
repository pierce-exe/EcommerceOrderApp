# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 

@author: Harkiran, Pierce, Jenita
"""
#List of imports needed for the code 
import socket 
import time 
import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


#Define a function local to the Purchaser that will verify a message based on the timestamp
def timestamp_verify(rectime):
    current_time = time.time() #get current timestamp in seconds
    
    if(current_time - rectime <= 60):
        #If the difference is 60 or less (ie one min has passed since message was sent), message is valid
        return True
    
    elif (current_time - rectime > 60):
        #If the different is greater than 60, (ie more than one minute passed since message was sent), message in invalid
        return False

#Initailize the RSA key-------------------------------------------------------
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

#The supervisor is a client to the OrderDept socket and the Purchaser socket---

#Connecting to the OrderDept socket 
s_order = socket.socket()             # Create a socket object
port = 60000                    # Reserve a port for your service.

s_order.connect(('127.0.0.1', port))

#Connecting to the Purchaser socket 
s_purch = socket.socket()             # Create a socket object
port = 30000                    # Reserve a port for your service.

s_purch.connect(('127.0.0.1', port))

##Initial key exchanage message------------------------------------------------
#Get public key of the Purchaser and OrderDept to encrypt the message
file_in = open("purchaser_public_key.pem", "rb")
pub_key_purch = file_in.read()
file_in.close()

file_in = open("orderDept_public_key.pem", "rb")
pub_key_order = file_in.read()
file_in.close()

#Initialize the public key objects 
pub_key_purch = RSA.importKey(pub_key_purch)
public_key_purch = PKCS1_OAEP.new(pub_key_purch)

pub_key_order = RSA.importKey(pub_key_order)
public_key_order = PKCS1_OAEP.new(pub_key_order)

#Generate a nonce, add identifier, timestamp and encrypt msg with private key 
nonce_super = ''.join([str(random.randint(0,9)) for i in range(8)])
key_msg1 = nonce_super + "SUPERVISOR" + str(time.time())

#Encrypt the plaintext key message 1 and send to the purchaser and order department
encrypt_key_msg1_purch = public_key_purch.encrypt(key_msg1.encode('utf-8'))
s_purch.send(encrypt_key_msg1_purch)

encrypt_key_msg1_order = public_key_order.encrypt(key_msg1.encode('utf-8'))
s_order.send(encrypt_key_msg1_order)



#Closing the s_order socket 
#s_order.close()

#Closing the s_purch socket
#s_purch.close()