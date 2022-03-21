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
from Crypto.Random import get_random_bytes
from decimal import Decimal


#Define a function local to the Purchaser that will verify a message based on the timestamp
def timestamp_verify(rectime):
    current_time = time.time() #get current timestamp in seconds
    if(Decimal(current_time) - Decimal(rectime) <= 60.00):
        #If the difference is 60 or less (ie one min has passed since message was sent), message is valid
        return True
    
    elif (Decimal(current_time) - Decimal(rectime) > 60.00):
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
port = 60001                    # Reserve a port for your service.

s_order.connect(('127.0.0.1', port))

#Connecting to the Purchaser socket 
s_purch = socket.socket()             # Create a socket object
port = 60002                    # Reserve a port for your service.

s_purch.connect(('127.0.0.1', port))

print("Connected as client to the order department and purchaser")

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

#Key exchange message 2 from Purchaser and Order department ------------------
msg2_purch = s_purch.recv(1024)
decrypt_key_msg2_purch = priv_key_super.decrypt(msg2_purch).decode('utf-8')
recv_nonce = decrypt_key_msg2_purch[:8]
if(recv_nonce != nonce_super):
    print("Invalid nonce received from purchaser")
    s_purch.close()
    
timestamp = decrypt_key_msg2_purch[16:]
valid_msg = timestamp_verify(timestamp)
if(not(valid_msg)):
    print("Invalid key exchange message2 received from purchaser")
    s_purch.close()
    
msg2_order = s_order.recv(1024)
decrypt_key_msg2_order = priv_key_super.decrypt(msg2_order).decode('utf-8')
recv_nonce = decrypt_key_msg2_order[:8]
if(recv_nonce != nonce_super):
    print("Invalid nonce recieved from order deparment")
    s_order.close()

timestamp = decrypt_key_msg2_order[16:]
valid_msg = timestamp_verify(timestamp)
if(not(valid_msg)):
    print("Invalid key exchange message2 received from order department")
    s_order.close()


#Key exchange message 3 send received nonce and session key ------------------
nonce_purch = decrypt_key_msg2_purch[8:15]
session_key_purch = get_random_bytes(8)

nonce_order = decrypt_key_msg2_order[8:15]
session_key_order = get_random_bytes(8)

key_msg3_purch = nonce_purch + str(session_key_purch) + str(time.time())
encrypt_msg3_purch = public_key_purch.encrypt(key_msg3_purch.encode('utf-8'))
s_purch.send(encrypt_msg3_purch)

key_msg3_order = nonce_order + str(session_key_order) + str(time.time())
encrypt_msg3_order = public_key_order.encrypt(key_msg3_order.encode('utf-8'))
s_order.send(encrypt_msg3_order)


#Closing the s_order socket 
#s_order.close()

#Closing the s_purch socket
#s_purch.close()