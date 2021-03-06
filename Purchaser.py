# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19

@author: Harkiran, Pierce, Jenita
"""

#List of imports needed for the code
from Crypto.Hash import SHA256
import socket 
import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
import time
from Crypto.Signature import PKCS1_v1_5
from decimal import Decimal


#Define a function local to the Purchaser that will verify a message based on the timestamp
def timestamp_verify(rectime):
    current_time = time.time() #get current timestamp in seconds
    print("Received time: ", rectime)
    print("Current time: ", current_time)
    
    if(Decimal(current_time) - Decimal(rectime) <= 60):
        #If the difference is 60 or less (ie one min has passed since message was sent), message is valid
        print("timestamp_verify returning true")
        return True
    
    elif (Decimal(current_time) - Decimal(rectime) > 60):
        #If the different is greater than 60, (ie more than one minute passed since message was sent), message in invalid
        print("timestamp_verify returning false")
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

while True:
    print("Waiting for order department to connect")
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
    key_msg3 = str(nonce_order) + str(time.time())
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
        
    timestamp = decrypted_key_msg3_super[8:]
    print("Key exchange message 3, supervisor timestamp:", timestamp)
    valid_msg = timestamp_verify(timestamp)
    if(not(valid_msg)):
        print("Invalid timestamp recieved from supervisor key exchange message 3")
        conn.close()
    
    #END OF KEY EXCHANGE ---------------------------------------------------
    #START OF ORDER --------------------------------------------------------
    # sign hashed order file using SHA-256
    order_file = "order.pdf" # location of order file
    BLOCK_SIZE = 65536  # The size of each read from the file
    signer = PKCS1_v1_5.new(key)
    digest = SHA256.new()

    with open(order_file, 'rb') as f:
        fb = f.read(BLOCK_SIZE)  # read from file
        while len(fb) > 0:
            digest.update(fb) # update hash
            fb = f.read(BLOCK_SIZE) # read next block
    sign_hashed_order_file = signer.sign(digest)
    print("Hashed and signed by the Purchaser using the Purchaser's private key")

    with open(order_file, 'rb') as file:
            original = file.read()
        
    # send length of signed file to supervisor
    length = len(original)
    conn.send((str(length)).encode())
    
    # send length of signed file to order department
    s_order.send((str(length)).encode())


    with open("file_with_hash.pdf", 'wb') as fh:
        fh.write("ORDER-1".encode())
        fh.write(original)
        fh.write(sign_hashed_order_file)

    # send signed file to supervisor
    myfile = open("file_with_hash.pdf", 'rb')
    l = myfile.read(1024)

    while l:
        # print("sending...")
        conn.send(l)
        l = myfile.read(1024)
    myfile.close()
    conn.shutdown(socket.SHUT_WR)
    print("Sent signed order file to Supervisor") 
    
    
    # send signed file to orderdepartment  
    myfile = open("file_with_hash.pdf", 'rb')
    line = myfile.read(1024)

    while line:
        # print("sending...")
        s_order.send(line)
        line = myfile.read(1024)
    myfile.close()
    s_order.shutdown(socket.SHUT_WR)
    print("Sent signed order file to Order Department")

    # ORDER COMPLETE-----------------------------------------------------------
    
    #Close the socket once the transmission is complete
    #Closing the socket where the Purchaser is the client, OrderDept is the server
    s_order.close();
    #Closing the conn socket (Purchase is server, Supervisor is client)
    conn.close();