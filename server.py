# CSNETWK S16
# Bernardo, Xian & Manlangit, Aila


import socket
import json
import os
import math
import sys

udp_host =  "127.0.0.1"
#socket.gethostbyname(socket.gethostname())
udp_port = 12345
ADDR = (udp_host,udp_port)

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

def calculate_packet_count(file_size, buffer_size):
    packet_count = math.ceil(file_size / buffer_size)
    return packet_count

def send_file(filename, buffer_size, addr):
    file_size = os.path.getsize(os.path.join('server/',filename))
    pck_count = calculate_packet_count(file_size, buffer_size)

    print("Sending file " + filename + " to " + str(addr))
    print("File size: " + str(file_size) + " bytes")
    print("Packet count: " + str(pck_count))

    try:
        #file size
        res['file_size'] = file_size

        #send packet count
        res['pck_count'] = pck_count

        #send file
        with open(os.path.join('server/',filename)) as f:
            file_data = f.read()

        res['file_data'] = file_data.decode('utf-8')

        print("File successfully sent to " + str(addr))
        return True
    except:
        print("Error sending file to " + str(addr))        
        return False
    
def recv_file (filename, file_data, addr):
    print("Receiving file " + filename + " from " + str(addr))

    try:
        #file details
        print("filename: " + filename)
        print("file size: " + str(len(file_data)) + " bytes")
        print(file_data)
        file_data = file_data.encode('utf-8')
        print("decoded data")
        #receive file
        with open(os.path.join('server/',filename), 'wb') as f:
            f.write(file_data)

        print("File successfully received from " + str(addr))
        return True
    except:
        print("Error receiving file from " + str(addr))        
        return False

try:
    sock.bind(ADDR)
except sock.error:
    print("Bind failed. Error: " + str(socket.error))
    exit()

guests = {}
users = {}

print("Server starting up...")
print("Server started up on IP: " + udp_host + " Port: " + str(udp_port))

#terms
# res = {"res": "nan"}
# for sending responses to client
# get res from server then apply if else statements in client
# e.g. if server_json['res'] == 'join_suc': print appropriate message

filenames = os.listdir(os.path.abspath('server'))
print("Current files: ")
print(filenames)

try:
    while True:
        print ("Waiting for client...")
        cmd = ""

        data, addr = sock.recvfrom(1024)	        #receive data from client
        
        try: 
            data = json.loads(data.decode('utf-8'))
        except:
            print("Invalid data received")

        try:
            cmd = data['cmd']

            if cmd == "join":
                ip = data['ip']
                port = data['port']
                port = int(port)
            elif cmd == "register":
                handle = data['handle']
            elif cmd == "store":
                filename = data['filename']
                file_data = data['file_data']
            elif cmd == "get":
                filename = data['filename']
        except:
            print("Invalid command received")

        res = {"res":"nan"}


        #/join <ip> <port>
        if cmd == "join":
            if ip == udp_host and port == udp_port and addr not in guests:
                #unregistered user
                guests[addr] = "guest"

                print("Guest successfully joined: " + str(addr))
                res["res"] = "conn_success"
            else:
                print("Invalid join request from: " + str(addr))
                res["res"] = "conn_fail"
        #/register <handle>
        elif cmd == "register":
            # Handle not taken and address does not already have a handle
            if handle not in users.values() and addr not in users.keys():
                guests[addr] = handle
                users[addr] = handle

                print("User successfully registered: " + str(addr))
                print("Current users: ", users, "\n")

                res["res"] = "reg_success"
            # Handle taken or address already has a handle
            else:
                print("Handle already taken or address already has a handle")

                res["res"] = "reg_fail"
        #/leave
        elif cmd == "leave":
            #In connection, guest
            if addr in guests.keys() and guests[addr] == "guest":
                print("Guest successfully left: " + str(addr))
                res["res"] = "leave_success"
                guests.pop(addr)
            #In connection, user
            elif addr in users.keys():
                client_leave = users[addr]
                print(client_leave + " successfully left: " + str(addr))
                print("Current users: ", users, "\n")

                output = {"ser_msg": client_leave + " has left the chat."}
                res["res"] = "leave_success"
                for key in users.keys():
                    sock.sendto(json.dumps(output).encode('utf-8'), key)
                guests.pop(addr)
            #Not in connection
            else:
                print("Client not in connection")

                res["res"] = "leave_fail"
        #/store <filename>
        elif cmd == "store":
            if filename in filenames:
                print("Filename already exists")
                res["res"] = "store_fail"
            else:
            #In connection, user
                if addr in users.keys():
                    print("User " + users[addr] + " wants to store " + filename)
                    if recv_file(filename, file_data, addr):
                        print("Successfully stored " + filename)
                        res['filename'] = filename
                        res["res"] = "store_success"
                    else:
                        print("Error storing " + filename)
                        res["res"] = "store_fail"
                elif addr in guests.keys():
                    print("Guest wants to store " + filename)
                    if recv_file(filename, file_data, addr):
                        print("Successfully stored " + filename)
                        res['filename'] = filename
                        res["res"] = "store_success"
                    else:
                        print("Error storing " + filename)
                        res["res"] = "store_fail"
                #Not in connection
                else:
                    print("Client not in connection")
                    res["res"] = "store_fail"
        #/get <filename>
        elif cmd == "get":
            if filename not in filenames:
                print("File not found")
                res["res"] = "get_fail"
            else:
            #In connection, user
                if addr in users.keys():
                    print("User " + users[addr] + " wants to get " + filename)
                    if send_file(filename, 1024, sock, addr):
                        print("Succesfully sent " + filename)
                        res["res"] = "get_success"
                    else:
                        print("Error sending " + filename)
                        res["res"] = "get_fail"
                #In connection, guest
                elif addr in guests.keys():
                    print("Guest wants to get " + filename)
                    if send_file(filename, 1024, sock, addr):
                        print("Successfully sent " + filename)
                        res["res"] = "get_success"
                    else:
                        print("Error sending " + filename)
                        res["res"] = "get_fail"
                #Not in connection
                else:
                    print("Client not in connection")
                    res["res"] = "get_fail"
        #/dir
        elif cmd == "dir":
            #In connection, user
            if addr in users.keys():
                print("User " + users[addr] + " wants to get directory")

                if filenames is not None:
                    res['filenames'] = filenames
                    res["res"] = "dir_success"
                else:
                    print("No files in the server")
                    res["res"] = "dir_fail"
            elif addr in guests.keys():
                print("Guest wants to get directory")
                if filenames is not None:
                    res['filenames'] = filenames
                    res["res"] = "dir_success"
                else:
                    print("No files in the server")
                    res["res"] = "dir_fail"
            #Not in connection
            else:
                print("Client not in connection")
                res["res"] = "dir_fail"

        jmsg = json.dumps(res).encode('utf-8')
        sock.sendto(jmsg, addr)

except KeyboardInterrupt:
    print("Program terminated.")
    sys.exit(0)
    
