from btle import Peripheral,BTLEException
import struct
import math
import pexpect
import binascii
import socketserver
import sqlite3
from threading import Thread

DB_STRING = "/root/smartlinkweb/my.db"
address=[]
address.clear()
conn=sqlite3.connect(DB_STRING)
c=conn.cursor()
for x in range (1,11):
    c.execute("SELECT value FROM user_string WHERE session_id=?", [x])
    address.append(c.fetchone()[0]+" random")

class service(socketserver.BaseRequestHandler):
    def handle(self):
        data = 'dummy'
        isConnected=False
        #print ("Client connected with: ", self.client_address)
        while len(data):
            data = self.request.recv(1024)
            if len(data)>0 and len(data)<5 and data[0]==99 and isConnected==False:  #Not null, its (C)onnect command, 4 len command
                if data[1]>=48 and data[1]<=57:
                    try:
                        bleconn = Peripheral(address[data[1]-48])
                    except BTLEException as e:
                        self.request.send(b'error connecting to device\r\n')
                        isConnected=False
                    else:
                        isConnected=True
                        self.request.send(b'connected\r\n')
                        bleconn.writeCharacteristic(0x000f,binascii.a2b_hex("0100"))
            if len(data)!=0 and isConnected==True:
                cmd=data.rstrip(b'\r\n')
                if cmd!=b'' and cmd[0]!=99 and cmd[0]!=100:  #if command is not (c)onnect or (d)isconnect
                    try:
                        notify=bleconn.writeCharacteristicWn(0x0011,cmd,True)
                    except BTLEException as e:
                        isConnected=False
                        self.request.send(b'error writing to device\r\n')
                    else:
                        isConnected=True
                        self.request.send(notify['d'][0])
                        self.request.send(b'\r\n')
            if len(data)>0 and len(data)<5 and data[0]==100 and isConnected==True:  #
                cmd=data.rstrip(b'\r\n')
                if cmd!=b'':
                    bleconn.disconnect()
                    self.request.send(b'disconnected\r\n')
                    isConnected=False
        #print("Client exited")
        if isConnected==True:
            bleconn.disconnect()
        self.request.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    # activate bluetooth
    resp=pexpect.spawn('hciconfig hci0 up')
    resp.expect('.*')
    #print ("Smartlink Server started at port 1520")
    server=ThreadedTCPServer(('',1520), service)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
