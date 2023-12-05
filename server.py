# CSNETWK S16
# Bernardo, Xian & Manlangit, Aila


import socket
import json
import os

udp_host = socket.gethostbyname(socket.gethostname())
udp_port = 12345
ADDR = (udp_host,udp_port)

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

def file_pck_count(filename, buffer_size):
    file_size = os.path.getsize(filename)

    pck_count = file_size//buffer_size

    if file_size%buffer_size:
        pck_count += 1

    return pck_count

def send_packet(data, sock, addr):
    sock.sendto(data, addr)

    while True:
        try:
            data, messenger = sock.recvfrom(1024)
            data = data.decode()

            if data == "ACK":
                break
        except:
            print("Error sending packet to " + str(addr))
            break

def send_file(filename, buffer_size, sock, addr):
    pck_count = file_pck_count(filename, buffer_size)

    print("Sending file " + filename + " to " + str(addr))
    print("File size: " + str(os.path.getsize(filename)) + " bytes")
    print("Packet count: " + str(pck_count))

    try:
        #send file size
        sock.sendto(str(os.path.getsize(filename)).encode('utf-8'), addr)

        #send packet count
        sock.sendto(str(pck_count).encode('utf-8'), addr)

        #send file
        with open(os.path.join('server/',filename), 'rb') as f:
            for i in range(pck_count):
                data = f.read(buffer_size)
                sock.sendto(data, addr)

        print("File successfully sent to " + str(addr))
        return True
    except:
        print("Error sending file to " + str(addr))        
        return False
    
def recv_file (filename, sock, addr):
    print("Receiving file " + filename + " from " + str(addr))

    try:
        #receive file size
        filename, addr = sock.recvfrom(1024)
        filename = filename.decode('utf-8')
        file_size = int(sock.recvfrom(1024)[0].decode('utf-8'))

        #receive packet count
        pck_count, addr = sock.recvfrom(1024)
        pck_count = int(pck_count.decode('utf-8'))

        print("File size: " + str(file_size) + " bytes")
        print("Packet count: " + str(pck_count))

        #receive file
        with open(os.path.join('server/',filename), 'wb') as f:
            data = b''
            while len(data) < file_size:
                chunk, addr = sock.recvfrom(1024)
                data += chunk

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

filenames = os.listdir(os.path.abspath('CSNETWK-FileExchangeSystem/server'))
#print("Current files: ")
#for file in filenames:
#    print(file)

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
            #Handle not taken
            if handle not in users.values():
                guests[addr] = handle
                users[addr] = handle

                print("User successfully registered: " + str(addr))
                print("Current users: ", users, "\n")

                res["res"] = "reg_success"
            #Handle taken
            else:
                print("Handle already taken")

                res["res"] = "reg_fail"
        #/leave
        elif cmd == "leave":
            #In connection, guest
            if addr in guests.keys() and guests[addr] == "guest":
                guests.pop(addr)
                print("Guest successfully left: " + str(addr))

                res["res"] = "leave_success"
            #In connection, user
            elif addr in users.keys():
                client_leave = users[addr]
                guests.pop(addr)

                print(client_leave + "successfully left: " + str(addr))
                print("Current users: ", users, "\n")

                output = {"ser_msg": client_leave + " has left the chat."}
                res["res"] = "leave_success"
                for key in users.keys():
                    sock.sendto(json.dumps(output).encode('utf-8'), key)
            #Not in connection
            else:
                print("Client not in connection")

                res["res"] = "leave_fail"
        #/store <filename>
        elif cmd == "store":
            #In connection, user
            if addr in users.keys():
                print("User " + users[addr] + " wants to store " + filename)
                if recv_file(filename, sock, addr):
                    print("Successfully stored " + filename)
                    res["res"] = "store_success"
                else:
                    print("Error storing " + filename)
                    res["res"] = "store_fail"
            elif addr in guests.keys():
                print("Guest wants to store " + filename)
                if recv_file(filename, sock, addr):
                    print("Successfully stored " + filename)
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
                    #Send Directory to client
                    server_message = f"\Server Directory:\n".encode('utf-8')
                    sock.sendto(server_message, addr)

                    # Send each filename
                    for file in filenames:
                        filename_encoded = file.encode('utf-8')
                        sock.sendto(filename_encoded, addr)
                else:
                    print("Error getting directory")
                    res["res"] = "dir_fail"
            elif addr in guests.keys():
                print("Guest wants to get directory")
                if filenames is not None:
                    #Send Directory to client
                    server_message = f"\Server Directory:\n".encode('utf-8')
                    sock.sendto(server_message, addr)

                    # Send each filename
                    for file in filenames:
                        filename_encoded = file.encode('utf-8')
                        sock.sendto(filename_encoded, addr)
                else:
                    print("Error getting directory")
                    res["res"] = "dir_fail"
            #Not in connection
            else:
                print("Client not in connection")
                res["res"] = "dir_fail"

        jmsg = json.dumps(res).encode('utf-8')
        sock.sendto(jmsg, addr)
except KeyboardInterrupt:
    print("Keyboard Interrupt. Exiting...")

    
