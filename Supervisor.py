# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 

@author: Harkiran, Pierce, Jenita
"""
#List of imports needed for the code 
from Crypto.Hash import SHA256
import socket 
import time 
import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5
from Crypto.Random import get_random_bytes
from decimal import Decimal


#Define a function local to the Purchaser that will verify a message based on the timestamp
def timestamp_verify(rectime):
    current_time = time.time() #get current timestamp in seconds
    print("Received time: ", rectime)
    print("Current time: ", current_time)
    current_time = time.time() #get current timestamp in seconds
    if(Decimal(current_time) - Decimal(rectime) <= 60.00):
        #If the difference is 60 or less (ie one min has passed since message was sent), message is valid
        print("timestamp_verify returning true")
        return True
    
    elif (Decimal(current_time) - Decimal(rectime) > 60.00):
        #If the different is greater than 60, (ie more than one minute passed since message was sent), message in invalid
        print("timestamp_verify returning false")
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
print("Sent initial key exchange message to the purchaser")

encrypt_key_msg1_order = public_key_order.encrypt(key_msg1.encode('utf-8'))
s_order.send(encrypt_key_msg1_order)
print("Sent initial key exchange message to the order department")

#Key exchange message 2 from Purchaser and Order department ------------------
msg2_purch = s_purch.recv(1024)
print("Recieved second key exchange message from purchaser")
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
print("Received second key message from order department")
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
nonce_purch = decrypt_key_msg2_purch[8:16]
print("Purchaser nonce:", nonce_purch)
session_key_purch = get_random_bytes(8)

nonce_order = decrypt_key_msg2_order[8:16]
print("Order department nonce:", nonce_order)

key_msg3_purch = str(nonce_purch) + str(time.time())
encrypt_msg3_purch = public_key_purch.encrypt(key_msg3_purch.encode('utf-8'))
s_purch.send(encrypt_msg3_purch)
print("Key exchange message 3, send to purchaser")

key_msg3_order = str(nonce_order) + str(time.time())
encrypt_msg3_order = public_key_order.encrypt(key_msg3_order.encode('utf-8'))
s_order.send(encrypt_msg3_order)
print("Key exchange message 3, send to order department")

# END OF KEY EXCHANGE ---------------------------------------------------------
# START OF ORDER --------------------------------------------------------------
# receive length of signed hash
length_of_original = s_purch.recv(1024)     # receives the length of the original message 
end_line = int(length_of_original.decode())

myfile =  open("received_order_file_with_hash.pdf",'wb') # create a local file to save the incoming data 
data = s_purch.recv(1024)
while data:
    # print("receiving...")
    myfile.write(data)
    data = s_purch.recv(1024)
myfile.close()
print("Received order from Purchaser")

#verify order
all_text = open("received_order_file_with_hash.pdf", 'rb').read()
orderID, original, signed_order = all_text[:7].decode(), all_text[7:end_line+7], all_text[end_line+7:] # split the orderID, original file content, hash
signer = PKCS1_v1_5.new(pub_key_purch)
digest = SHA256.new()
digest.update(original)
if not signer.verify(digest, signed_order):  # verification 
    print("Verification failed!")
    s_purch.close()
print("Verification of order is successful!")

#approve order
approved_order_details = orderID + "T" + "SUPERVISOR" # orderID: ORDER-1 
encrypt_approval = public_key_order.encrypt(approved_order_details.encode('utf-8')) # encrypt the approval message with order dept's public key
s_order.send(encrypt_approval)  # send approval to order dept
print("Approval Sent to Order Department")

# ORDER COMPLETE-------------------------------------------------------------------------

#Closing the s_purch socket where the Supervisor is a client, Purchaser is a server
s_purch.close()

#Closing the s_order socket where the Supervisor is a client, OrderDept is a server
s_order.close()