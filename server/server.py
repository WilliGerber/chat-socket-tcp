import socket
import threading
import json
import base64
import datetime
from common.protocol import create_message, parse_message

HOST = '0.0.0.0'
PORT = 10000
clients = {}  # apelido: (socket, address)
groups = {"ALL": []}
log_file = "server_log.txt"

def log_action(ip_from, name_from, ip_to, name_to, action):
    timestamp = datetime.datetime.now().strftime('%d/%m/%Y; %H:%M')
    with open(log_file, "a") as log:
        log.write(f"{timestamp}; {ip_from}; {name_from}; {ip_to}; {name_to}; {action}\n")

def handle_client(client_socket, addr):
    try:
        data = client_socket.recv(4096)
        user = parse_message(data)
        nickname = user["from"]
        clients[nickname] = (client_socket, addr)
        groups["ALL"].append(nickname)
        log_action(addr[0], nickname, "TODOS", "TODOS", "login")
        broadcast_status()

        while True:
            data = client_socket.recv(65536)
            if not data:
                break
            msg = parse_message(data)
            if msg["type"] == "message":
                for target in msg["to"]:
                    if target in clients:
                        clients[target][0].send(data)
                log_action(addr[0], msg["from"], ",".join([clients[t][1][0] for t in msg["to"]]), ",".join(msg["to"]), f"msg:{msg['message']}")
            elif msg["type"] == "file":
                for target in msg["to"]:
                    if target in clients:
                        clients[target][0].send(data)
                log_action(addr[0], msg["from"], ",".join([clients[t][1][0] for t in msg["to"]]), ",".join(msg["to"]), f"arq:{msg['message']}")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        if nickname in clients:
            del clients[nickname]
            groups["ALL"].remove(nickname)
            log_action(addr[0], nickname, "TODOS", "TODOS", "logoff")
            broadcast_status()
        client_socket.close()

def broadcast_status():
    online_list = list(clients.keys())
    message = create_message("status", "server", ["ALL"], message=json.dumps(online_list))
    for user, (sock, _) in clients.items():
        try:
            sock.send(message)
        except:
            continue

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Servidor ouvindo em {HOST}:{PORT}...")

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

if __name__ == '__main__':
    start_server()