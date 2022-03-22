# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19

@author: Harkiran, Pierce, Jenita
"""

#List of imports needed for the code 
import socket 
import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
import time
from decimal import Decimal


#Define a function local to the Purchaser that will verify a message based on the timestamp
def timestamp_verify(rectime):
    current_time = time.time() #get current timestamp in seconds
    
    if(Decimal(current_time) - Decimal(rectime) <= 60):
        #If the difference is 60 or less (ie one min has passed since message was sent), message is valid
        return True
    
    elif (Decimal(current_time) - Decimal(rectime) > 60):
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
port = 60002                    # Reserve a port for your service.
s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
print(host)
s.bind(('127.0.0.1', port))            # Bind to the port
s.listen(5)                     # Now wait for client connection.
print("Waiting for order department to connect")

while True:
    conn, addr = s.accept()     # Establish connection with client.
    print("Accepted connection request from order department")
    
    #Connect to the socket of the OrderDept when sending an order
    #Connecting to the OrderDept socket 
    s_order = socket.socket()             # Create a socket object
    port = 60000                    # Reserve a port for your service.
    
    s_order.connect(('127.0.0.1', port))

    #Get public key of the Supervisor and OrderDept to encrypt messages
    file_in = open("supervisor_public_key.pem", "rb")
    pub_key_super = file_in.read()
    file_in.close()

    file_in = open("orderDept_public_key.pem", "rb")
    pub_key_order = file_in.read()
    file_in.close()

    #Initialize the public key objects 
    pub_key_super = RSA.importKey(pub_key_super)
    public_key_super = PKCS1_OAEP.new(pub_key_super)

    pub_key_order = RSA.importKey(pub_key_order)
    public_key_order = PKCS1_OAEP.new(pub_key_order)
    
    #Initial key exchange message -------------------------------------------
    #Send an initial message to the order department 
    nonce_purch = ''.join([str(random.randint(0,9)) for i in range(8)])
    key_msg1 = nonce_purch + "PURCHASER" + str(time.time())
    
    encrypt_key_msg1_order = public_key_order.encrypt(key_msg1.encode('utf-8'))
    s_order.send(encrypt_key_msg1_order)
    print("Sent initial key exchange message to order department")

    #Receive msg1 key exchange from supervisor -------------------------------
    rec_msg1 = conn.recv(1024) 
    print("Received initial key exchange message from supervisor")
    
    #Decrypt the message with private key 
    decrypted_key_msg1_super = priv_key_purch.decrypt(rec_msg1).decode('utf-8')
    timestamp = decrypted_key_msg1_super[18:]
    valid_msg = timestamp_verify(timestamp)
    if(not(valid_msg)):
        print("Invalid initial key exchange message recieved from supervisor")
        conn.close()
        
    super_nonce = decrypted_key_msg1_super[:8]
    
    #Key exchange message 2: Send back to supervisor--------------------------
    key_msg2 = super_nonce + nonce_purch + str(time.time())
    encrypt_msg2_super = public_key_super.encrypt(key_msg2.encode('utf-8'))
    conn.send(encrypt_msg2_super)
    print("Sent key exchange message 2 to the supervisor")
    
    #Recieve msg2 key exchange from order department--------------------------
    rec_msg2 = s_order.recv(1024)
    print("Recieved key exchange message 2 from the order department")
    
    #Decrypt the message with private key 
    decrypted_key_msg2_order = priv_key_purch.decrypt(rec_msg2).decode('utf-8')
    recv_nonce = decrypted_key_msg2_order[:8]
    if(recv_nonce != nonce_purch):
        print("Invalid nonce recieved from order department")
        s_order.close()
        
    timestamp = decrypted_key_msg2_order[16:]
    valid_msg = timestamp_verify(timestamp)
    if(not(valid_msg)):
        print("Invalid key exchange message2 recieved from order department")
        s_order.close()
        
    #Key exchange message 3 with order department-----------------------------    
    #Send new message with the recieved nonce, session key and new timestamp
    nonce_order = decrypted_key_msg2_order[8:16]
    session_key_order = get_random_bytes(8)
    key_msg3 = nonce_order + str(session_key_order) + str(time.time())
    encrypt_msg3_order = public_key_order.encrypt(key_msg3.encode('utf-8'))
    s_order.send(encrypt_msg3_order)    
    print("Sent key exchange message 3 to the order department")
    
    #Received key exchange message 3 with supervisor -------------------------
    rec_msg3 = conn.recv(1024)
    print("Received key exchange message 3 from the supervisor")
        
    #Decrypt the message with private key 
    decrypted_key_msg3_super = priv_key_purch.decrypt(rec_msg3).decode('utf-8')
    
    #Check the nonce in the message 
    rec_nonce = decrypted_key_msg3_super[:8]
    if(rec_nonce != nonce_purch):
        print("Invalid nonce received from supervisor")
        conn.close()
        
    timestamp = decrypted_key_msg3_super[16:]
    valid_msg = timestamp_verify(timestamp)
    if(not(valid_msg)):
        print("Invalid initial key exchange message recieved from supervisor")
        conn.close()
    
    session_key_super = decrypted_key_msg3_super[8:16]
    
    #Close the socket once the transmission is complete
    #conn.close();