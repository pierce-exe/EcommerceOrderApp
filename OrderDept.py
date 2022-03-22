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
import time
from decimal import Decimal

#Define a function local to the OrderDept that will verify a message based on the 

def timestamp_verify(rectime):
    current_time = time.time() #get current timestamp in seconds
    print("Received time: ", rectime)
    print("Current time: ", current_time)
    
    if(Decimal(current_time) - Decimal(rectime) <= 60):
        #If the difference is 60 or less (ie one min has passed since message was sent), message is valid
        print("timestamp_verify returning true")
        return True
    
    elif (Decimal(current_time) - Decimal(rectime) > 60.00):
        #If the different is greater than 60, (ie more than one minute passed since message was sent), message in invalid
        print("timestamp_verify returning false")
        return False

#Initailize the RSA key
key = RSA.generate(2048)

#Generate private key 
private_key = key.export_key()
priv_key_order = RSA.importKey(private_key)
priv_key_order = PKCS1_OAEP.new(priv_key_order)
    
#Generate public key 
public_key = key.publickey().export_key()
pub_key_order = RSA.importKey(public_key)
public_key_order = PKCS1_OAEP.new(pub_key_order)
    
#Write the public key to the .pem file, accessible by Supervisor and Purchaser
file_out = open("orderDept_public_key.pem", "wb")
file_out.write(public_key)
file_out.close()

#Creating a second TCP socket for the supervisor to connect to 
port = 60001                    # Reserve a port for your service.
s_super = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
print(host)
s_super.bind(('127.0.0.1', port))            # Bind to the port
s_super.listen(5)                     # Now wait for client connection.
print("Waiting for supervisor client to connect")

#The order department acts as a server, the purchaser and supervisor both connect to the socket 
port = 60000                    # Reserve a port for your service.
s_purch = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
print(host)
s_purch.bind(('127.0.0.1', port))            # Bind to the port
s_purch.listen(5)                     # Now wait for client connection.
print("Waiting for purchaser client to connect")


while True:
    conn_purch, addr = s_purch.accept()     # Establish connection with client.
    print("Accepted connection request from purchaser client")
    
    conn_super, addr = s_super.accept() #Establish connection with client
    print("Accepted connection request from supervisor client")
    
    #Get public key of the Purchaser and Supervisor to encrypt messages
    file_in = open("purchaser_public_key.pem", "rb")
    pub_key_purch = file_in.read()
    file_in.close()

    file_in = open("supervisor_public_key.pem", "rb")
    pub_key_super = file_in.read()
    file_in.close()

    #Initialize the public key objects 
    pub_key_purch = RSA.importKey(pub_key_purch)
    public_key_purch = PKCS1_OAEP.new(pub_key_purch)
    
    pub_key_super = RSA.importKey(pub_key_super)
    public_key_super = PKCS1_OAEP.new(pub_key_super)
 
    #Recieve key exchange msg 1 from both clients
    rec_msg1_purch = conn_purch.recv(1024)    
    print("OrderDept recieved message1 from purchaser")

    #Decrypt messages with private key 
    decrypted_key_msg1_purch = priv_key_order.decrypt(rec_msg1_purch).decode('utf-8')
    timestamp = decrypted_key_msg1_purch[17:]
    valid_msg1 = timestamp_verify(timestamp)
    if(not(valid_msg1)):
        print("Invalid timestamp recieved from purchaser in key exchange message 1")
        conn_purch.close()
    
    rec_msg1_super = conn_super.recv(1024)
    print("OrderDept recieved message1 from supervisor")
    #Decrypt messages with private key 
    decrypted_key_msg1_super = priv_key_order.decrypt(rec_msg1_super).decode('utf-8')
    timestamp = decrypted_key_msg1_super[18:]
    valid_msg1 = timestamp_verify(timestamp)
    print("Timestamp_verify output: ", valid_msg1)
    if(not(valid_msg1)):
        print("Invalid timestamp recieved from supervisor in key exchange message 1")
        conn_super.close()
        
    #Save received nonce of purchaser and supervisor 
    purch_nonce = decrypted_key_msg1_purch[:8]
    super_nonce = decrypted_key_msg1_super[:8]
    
    nonce_order = ''.join([str(random.randint(0,9)) for i in range(8)])
    
    #Key exchange message 2: Send back to supervisor and purchaser------------
    key_msg2_purch = purch_nonce + nonce_order + str(time.time())
    encrypt_msg2_purch = public_key_purch.encrypt(key_msg2_purch.encode('utf-8'))
    conn_purch.send(encrypt_msg2_purch)
    print("Sent key exchange message to the purchaser")
    
    key_msg2_super = super_nonce + nonce_order + str(time.time())
    encrypt_msg2_super = public_key_super.encrypt(key_msg2_super.encode('utf-8'))
    conn_super.send(encrypt_msg2_super)
    print("Sent key exchange message to the supervisor")
    
    #Recieving key exchange message 3 from supervisor and purchaser ----------
    rec_msg3_super = conn_super.recv(1024)
    #Decrypt messages with private key 
    decrypted_key_msg3_super = priv_key_order.decrypt(rec_msg3_super).decode('utf-8')
    
    rec_nonce = decrypted_key_msg3_super[:8]
    if(rec_nonce != nonce_order):
        print("Incorrect nonce received from supervisor in key exchange message 3")
        conn_super.close()
    
    timestamp = decrypted_key_msg3_super[18:]
    print("Message3 timestamp from supervisor: ", timestamp)
    valid_msg1 = timestamp_verify(timestamp)
    if(not(valid_msg1)):
        print("Invalid timestamp received from supervisor in key exchange message 3")
        conn_super.close()
        
    #Save the session key received by the supervisor 
    session_key_super = decrypted_key_msg3_super[8:16]
    
    #Receiving message 3 from the purchaser
    rec_msg3_purch = conn_purch.recv(1024)
    #Decrypt messages with private key 
    decrypted_key_msg3_purch = priv_key_order.decrypt(rec_msg3_purch).decode('utf-8')
    
    rec_nonce = decrypted_key_msg3_purch[:8]
    if(rec_nonce != nonce_order):
        print("Incorrect nonce received from supervisor")
        conn_purch.close()
    
    timestamp = decrypted_key_msg3_purch[16:]
    valid_msg1 = timestamp_verify(timestamp)
    if(not(valid_msg1)):
        print("Invalid initial key exchange message recieved from supervisor")
        conn_purch.close()
        
    #Save the session key received by the supervisor 
    session_key_purch = decrypted_key_msg3_purch[8:16]     
    
    
    #Close the socket once the transmission is complete
    #conn.close();