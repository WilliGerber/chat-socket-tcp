import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import base64
import json
from common.protocol import create_message, parse_message

class ClientApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Cliente TCP")
        self.sock = None
        self.nickname = ""
        self.connected = False

        self.setup_gui()

    def setup_gui(self):
        self.top_frame = tk.Frame(self.master)
        self.top_frame.pack(pady=5)

        tk.Label(self.top_frame, text="Apelido:").pack(side=tk.LEFT)
        self.nickname_entry = tk.Entry(self.top_frame)
        self.nickname_entry.pack(side=tk.LEFT)

        self.connect_btn = tk.Button(self.top_frame, text="Conectar", command=self.connect)
        self.connect_btn.pack(side=tk.LEFT)

        self.disconnect_btn = tk.Button(self.top_frame, text="Desconectar", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT)

        self.users_list = tk.Listbox(self.master, selectmode=tk.MULTIPLE, height=5)
        self.users_list.pack(fill=tk.X, padx=5)

        self.chat_display = scrolledtext.ScrolledText(self.master, height=10)
        self.chat_display.pack(fill=tk.BOTH, padx=5, pady=5)

        self.message_entry = tk.Entry(self.master)
        self.message_entry.pack(fill=tk.X, padx=5)
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.bottom_frame = tk.Frame(self.master)
        self.bottom_frame.pack(pady=5)

        tk.Button(self.bottom_frame, text="Enviar", command=self.send_message).pack(side=tk.LEFT)
        tk.Button(self.bottom_frame, text="Enviar Arquivo", command=self.send_file).pack(side=tk.LEFT)

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", 10000))
        self.nickname = self.nickname_entry.get()
        if not self.nickname:
            messagebox.showerror("Erro", "Insira um apelido")
            return
        self.sock.send(create_message("login", self.nickname, ["server"]))
        self.connected = True
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        threading.Thread(target=self.listen_server, daemon=True).start()

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None
        self.connected = False
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.chat_display.insert(tk.END, "Desconectado.\n")

    def listen_server(self):
        try:
            while self.connected:
                data = self.sock.recv(65536)
                if not data:
                    break
                msg = parse_message(data)
                if msg["type"] == "message":
                    self.chat_display.insert(tk.END, f"{msg['from']}: {msg['message']}\n")
                elif msg["type"] == "file":
                    self.save_file(msg)
                elif msg["type"] == "status":
                    self.update_user_list(json.loads(msg["message"]))
        except Exception as e:
            print("Erro na escuta:", e)

    def update_user_list(self, users):
        self.users_list.delete(0, tk.END)
        for user in users:
            if user != self.nickname:
                self.users_list.insert(tk.END, user)

    def get_selected_users(self):
        selected = self.users_list.curselection()
        return [self.users_list.get(i) for i in selected] or ["ALL"]

    def send_message(self):
        text = self.message_entry.get()
        if text:
            msg = create_message("message", self.nickname, self.get_selected_users(), message=text)
            self.sock.send(msg)
            self.message_entry.delete(0, tk.END)

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            file_name = os.path.basename(file_path)
            msg = create_message("file", self.nickname, self.get_selected_users(), message=file_name, file_content=content)
            self.sock.send(msg)

    def save_file(self, msg):
        directory = filedialog.askdirectory()
        if not directory:
            return
        file_path = os.path.join(directory, "new_" + msg["message"])
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(msg["file_content"]))
        self.chat_display.insert(tk.END, f"{msg['from']} enviou arquivo: {msg['message']}\n")

if __name__ == '__main__':
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
