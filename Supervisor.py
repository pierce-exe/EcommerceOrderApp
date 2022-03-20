# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 

@author: Harkiran, Pierce, Jenita
"""
#List of imports needed for the code 
import socket 

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