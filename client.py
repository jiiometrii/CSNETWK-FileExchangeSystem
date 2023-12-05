import datetime
import socket
import json
import threading
import time
import queue

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345

def print_menu():
    print("Command Menu:")
    print("To join a server: /join <server_ip_add> <port>")
    print("To leave a server: /leave")
    print("To register a handle: /register <handle>")
    print("To store a file in the server: /store <filename>")
    print("To get the list of files: /dir")
    print("To get a file in the server: /get <filename>")
    print("To see all commands: /?")

class Client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.exit_event = threading.Event()
        self.message_queue = queue.Queue()
        self.print_lock = threading.Lock()
        self.handle = None

    def send_command(self, command):
        try:
            cmd_parts = command.split()
            self.cmd_name = cmd_parts[0][1:]  
            cmd_data = {"cmd": self.cmd_name}

            if self.cmd_name == "dir":
                pass
            elif self.cmd_name == "leave":
                cmd_data["handle"] = self.handle
            elif len(cmd_parts) < 2:
                print("Invalid command. Please enter a valid command.")
                return
            else:
                if self.cmd_name == "join":
                    if len(cmd_parts) < 3:
                        print("Invalid command. Please enter a valid IP and port.")
                        return
                    cmd_data["ip"] = cmd_parts[1]
                    cmd_data["port"] = cmd_parts[2]
                elif self.cmd_name == "register":
                    self.handle = cmd_parts[1]
                    cmd_data["handle"] = self.handle
                elif self.cmd_name == "store":
                    filename = cmd_parts[1]
                    with open(filename, 'rb') as f:
                        file_data = f.read()
                    cmd_data["filename"] = filename
                    cmd_data["file_data"] = file_data.decode('utf-8')
                elif self.cmd_name == "get":
                    cmd_data["filename"] = cmd_parts[1]

            with self.print_lock:
                while not self.message_queue.empty():
                    print(self.message_queue.get())

            self.sock.sendto(json.dumps(cmd_data).encode(), (SERVER_IP, SERVER_PORT))

        except FileNotFoundError:
            self.message_queue.put(f'File {filename} not found')
        except OSError as e:
            if self.cmd_name == "join":
                self.message_queue.put('Failed to connect to the server. Please check the server IP and port.')
            elif self.cmd_name == "leave":
                self.message_queue.put('You are not connected to a server.')
            else:
                self.message_queue.put(f'Error sending command: {e}')
        
    def receive_responses(self):
        while not self.exit_event.is_set():
            try:
                data, server = self.sock.recvfrom(1024)
                if data:
                    try:
                        response = json.loads(data.decode())
                        if 'res' in response:
                            if response['res'] == 'conn_success':
                                self.message_queue.put('Successfully joined the server.\n')
                            elif response['res'] == 'conn_fail':
                                self.message_queue.put('Failed to join the server.\n')
                            elif response['res'] == 'reg_success':
                                self.message_queue.put(f'Welcome {self.handle}!\n')
                            elif response['res'] == 'reg_fail':
                                self.message_queue.put('Failed to register. Handle may exist or user already has handle.\n')
                            elif response['res'] == 'leave_success':
                                self.message_queue.put('Successfully left the server.\n')
                            elif response['res'] == 'leave_fail':
                                self.message_queue.put('Failed to leave the server.\n')
                            elif response['res'] == 'store_success':
                                filename = response['filename']
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                handle = self.handle if self.handle else "User"
                                self.message_queue.put(f'{handle} <{timestamp}>: Uploaded {filename}\n')
                            elif response['res'] == 'store_fail':
                                self.message_queue.put('Failed to store the file.\n')
                            elif response['res'] == 'get_success':
                                filename = response['filename']
                                file_data = response['file_data']
                                self.message_queue.put("Receiving file " + filename + " from server")
                                try:
                                    #file details
                                    self.message_queue.put("filename: " + filename)
                                    self.message_queue.put("file size: " + str(len(file_data)) + " bytes")
                                    file_data = file_data.encode('utf-8')
                                    print("decoded data")
                                    #receive file
                                    with open(filename, 'wb') as f:
                                        f.write(file_data)
                                    self.message_queue.put('Successfully got the file.\n')
                                except:
                                    self.message_queue.put('Error getting the file.\n')
                            elif response['res'] == 'get_fail':
                                self.message_queue.put('Failed to get the file from server.\n')
                            elif response['res'] == 'dir_success':
                                self.message_queue.put('System Directory:\n')
                                if 'filenames' in response:
                                    for filename in response['filenames']:
                                        self.message_queue.put(filename)
                                    self.message_queue.put('\n')
                                else:
                                    self.message_queue.put('No filenames received in dir_success response\n')
                            elif response['res'] == 'dir_fail':
                                self.message_queue.put('Failed to get the directory.\n')
                        elif 'file_data' in response and 'filename' in response:
                            filename = response['filename']
                            file_data = response['file_data'].encode('utf-8')
                            with open(filename, 'wb') as f:
                                f.write(file_data)
                            self.message_queue.put(f'File received from Server: {filename}\n')
                        else:
                            self.message_queue.put(f'Received: {data.decode()}\n')
                    except json.JSONDecodeError:
                        message = data.decode()
                        self.message_queue.put('Received a non-JSON message: {}\n'.format(data.decode()))
                time.sleep(1)
            except socket.timeout:
                if self.cmd_name == "join":
                    self.message_queue.put('Failed to connect to the server. Please check the server IP and port.\n')
                else:
                    self.message_queue.put('No data received. Waiting...\n')
                    time.sleep(1)
            except socket.error as e:
                self.message_queue.put(f'Error sending command: {e}\n')

    def start(self):
        threading.Thread(target=self.receive_responses).start()
        threading.Thread(target=self.print_messages).start()

    def stop(self):
        self.exit_event.set()

    def print_messages(self):
        while not self.exit_event.is_set():
            with self.print_lock:
                while not self.message_queue.empty():
                    print(self.message_queue.get())
            time.sleep(0.1)

def main():
    client = None

    while True:
        if client is None:
            print_menu()
        command = input('Enter command: ')
        if command.startswith('/join'):
            if client is None:
                client = Client()
                client.start()
            client.send_command(command)
        elif command == '/leave':
            if client is not None:
                client.send_command(command)
                time.sleep(0.5)
                client.stop()
                client = None
            else:
                print("You are not connected to a server\n")
        elif command == '/?':
            if client is not None:
                print_menu()
        elif command.startswith('/'):
            if client is not None:
                client.send_command(command)
            else:
                print("You are not connected to a server\n")
        else:
            print("Invalid command\n")

        if client is not None:
            while not client.message_queue.empty():
                print(client.message_queue.get())
        time.sleep(0.1)

if __name__ == '__main__':
    main()