import socket
import json
import threading
import time
import signal

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

    def send_command(self, command):
        try:
            cmd_parts = command.split()
            cmd_name = cmd_parts[0][1:]  
            cmd_data = {"cmd": cmd_name}

            if cmd_name == "join":
                cmd_data["ip"] = cmd_parts[1]
                cmd_data["port"] = cmd_parts[2]
            elif cmd_name == "register":
                cmd_data["handle"] = cmd_parts[1]
            elif cmd_name == "store":
                filename = cmd_parts[1]
                with open(filename, 'rb') as f:
                    file_data = f.read()
                cmd_data["filename"] = filename
                cmd_data["file_data"] = file_data.decode('utf-8', 'ignore')
            elif cmd_name == "get":
                cmd_data["filename"] = cmd_parts[1]
            elif cmd_name == "dir":
                pass 

            self.sock.sendto(json.dumps(cmd_data).encode(), (SERVER_IP, SERVER_PORT))
        except FileNotFoundError:
            print(f'File {filename} not found')
        except socket.error as e:
            print(f'Error sending command: {e}')
        
    def receive_responses(self):
        while not self.exit_event.is_set():
            try:
                data, server = self.sock.recvfrom(1024)
                print(f'Received: {data.decode()}')
                time.sleep(1)
            except socket.timeout:
                print('No data received. Waiting...')
                time.sleep(1)
            except socket.error as e:
                print(f'Error receiving data: {e}')

    def start(self):
        threading.Thread(target=self.receive_responses).start()

    def stop(self):
        self.exit_event.set()

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
            client.send_command(command)  # Add this line
            print("JOINED")
        elif command == '/?':
            print_menu()
        elif command in ['/leave', '/register', '/store', '/dir']:
            print("You are not connected to a server")
        elif command == '/quit':
            break
        elif client is not None:
            client.send_command(command)
        else:
            print("Invalid command")

    while not leave:
        command = input('Enter command: ')
        if command == '/leave':
            leave = True
            print("LEFT")
        elif command == '/?':
            print_menu()
        elif command == "/join":
            print("You are already connected to a server")
        elif command == '/quit':
            break
        elif command.startswith('/'):
            if client is not None:
                client.send_command(command)
            else:
                print("You are not connected to a server")
        else:
            print("Invalid command")

    if client is not None:
        client.stop()

if __name__ == '__main__':
    main()