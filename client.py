import datetime
import socket
import json
import threading
import time
import queue

SERVER_IP = '192.168.254.110'
SERVER_PORT = 12345

def print_menu():
    print("Command Menu:")
    print("To join a server: /join <server_ip_add> <port>")
    print("To leave a server: /leave")
    print("To register a handle: /register <handle>")
    print("To message all users: /store <filename>")
    print("To message one user: /dir")
    print("To see all commands: /?")
    print("To end program: /quit\n")

class Client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.exit_event = threading.Event()
        self.message_queue = queue.Queue()
        self.print_lock = threading.Lock()

    def send_command(self, command):
        try:
            cmd_parts = command.split()
            self.cmd_name = cmd_parts[0][1:]  
            cmd_data = {"cmd": self.cmd_name}

            if self.cmd_name == "join":
                cmd_data["ip"] = cmd_parts[1]
                cmd_data["port"] = cmd_parts[2]
            elif self.cmd_name == "register":
                self.handle = cmd_parts[1]  # Store the handle
                cmd_data["handle"] = self.handle
            elif self.cmd_name == "store":
                filename = cmd_parts[1]
                with open(filename, 'rb') as f:
                    file_data = f.read()
                cmd_data["filename"] = filename
                cmd_data["file_data"] = file_data.decode('utf-8', 'ignore')
            elif self.cmd_name == "get":
                cmd_data["filename"] = cmd_parts[1]
            elif self.cmd_name == "dir":
                pass 

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
                                self.message_queue.put('Successfully joined the server.')
                            elif response['res'] == 'conn_fail':
                                self.message_queue.put('Failed to join the server.')
                            elif response['res'] == 'reg_success':
                                self.message_queue.put(f'Welcome {self.handle}!')
                            elif response['res'] == 'reg_fail':
                                self.message_queue.put('Failed to register. Handle may already exist.')
                            elif response['res'] == 'leave_success':
                                self.message_queue.put('Successfully left the server.')
                            elif response['res'] == 'leave_fail':
                                self.message_queue.put('Failed to leave the server.')
                            elif response['res'] == 'store_success':
                                filename = response['filename']
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                self.message_queue.put(f'{self.handle}<{timestamp}>: Uploaded {filename}')
                            elif response['res'] == 'store_fail':
                                self.message_queue.put('Failed to store the file.')
                            elif response['res'] == 'get_success':
                                self.message_queue.put('Successfully got the file.')
                            elif response['res'] == 'get_fail':
                                self.message_queue.put('Failed to get the file from server.')
                            elif response['res'] == 'dir_fail':
                                self.message_queue.put('Failed to get the directory.')
                        elif 'file_data' in response and 'filename' in response:
                            filename = response['filename']
                            file_data = response['file_data'].encode('utf-8')
                            with open(filename, 'wb') as f:
                                f.write(file_data)
                            self.message_queue.put(f'File received from Server: {filename}')
                        else:
                            self.message_queue.put(f'Received: {data.decode()}')
                    except json.JSONDecodeError:
                        message = data.decode()
                        self.message_queue.put('Received a non-JSON message: {}'.format(data.decode()))
                time.sleep(1)
            except socket.timeout:
                if self.cmd_name == "join":
                    self.message_queue.put('Failed to connect to the server. Please check the server IP and port.')
                else:
                    self.message_queue.put('No data received. Waiting...')
                    time.sleep(1)
            except socket.error as e:
                self.message_queue.put(f'Error sending command: {e}')

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
    join = False
    leave = False
    client = None

    while not join:
        print_menu()
        command = input('Enter command: ')
        if command.startswith('/join'):
            client = Client()
            client.start()
            join = True
            client.send_command(command)
        elif command == '/?':
            print_menu()
        elif command in ['/leave', '/register', '/store', '/dir']:
            print("You are not connected to a server\n")
        elif client is not None:
            client.send_command(command)
        else:
            print("Invalid command\n")

        if client is not None:
            while not client.message_queue.empty():
                print(client.message_queue.get())
        time.sleep(0.1)

    while not leave:
        command = input('Enter command: ')
        if command == '/leave':
            leave = True
            client.message_queue.put("Connection terminated")
        elif command == '/?':
            print_menu()
        elif command == "/join":
            client.message_queue.put("You are already connected to a server")
        elif command.startswith('/'):
            if client is not None:
                client.send_command(command)
            else:
                print("You are not connected to a server\n")
        else:
            client.message_queue.put("Invalid command")

        if client is not None:
            while not client.message_queue.empty():
                print(client.message_queue.get())
        time.sleep(2)

if __name__ == '__main__':
    main()