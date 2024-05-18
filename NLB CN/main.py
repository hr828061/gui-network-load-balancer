import tkinter as tk
import socket as s
import random
import queue
from tkinter import messagebox
import math
from tkinter import ttk
from collections import deque
import time
import re
port_number = 10000
host = 'localhost'


def resize_image(image, width, height):
    return image.subsample(max(image.width() // width, 1), max(image.height() // height, 1))


class MainMenu:  # for the functionalities of main screen...
    def __init__(self):
        self.root = tk.Tk()
        self.DisplayMenu()

    def CloseWindow(self):
        self.root.destroy()

    def DisplayMenu(self):
        self.root.geometry("900x900")
        self.root.title("Main Menu")
        self.root.protocol("WM_DELETE_WINDOW", self.CloseWindow)
        self.root.configure(bg="Black")
        title_lbl = tk.Label(self.root, text="CL3001 - Computer Networks Lab", font=('Century Schoolbook', 25))
        title_lbl.config(bg="Black", fg="White")
        title_lbl.place(x=200, y=100)
        title_lbl2 = tk.Label(self.root, text="Network Load Balancer", font=('Century Schoolbook', 25))
        title_lbl2.config(bg="Black", fg="White")
        title_lbl2.place(x=280, y=160)
        title_lbl2 = tk.Label(self.root, text="Semester Project", font=('Century Schoolbook', 25))
        title_lbl2.config(bg="Black", fg="White")
        title_lbl2.place(x=325, y=220)
        grp1 = tk.Label(self.root, text="Huzaifa Zulfiqar   21K-3010", font=('Century Schoolbook', 13))
        grp2 = tk.Label(self.root, text="Omer Shoaib  21K-3066", font=('Century Schoolbook', 13))
        grp1.config(bg="Black", fg="White")
        grp2.config(bg="Black", fg="White")
        grp1.place(x=650, y=610)
        grp2.place(x=650, y=640)
        ch_btn = tk.Button(self.root, text="Initialize Load Balancer", font=('Century Gothic', 18),
                           command=self.get_input)
        ch_btn.place(x=300, y=350)
        self.root.mainloop()

    def get_input(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        label = ttk.Label(self.root, text="Enter the configurations for network: ",
                          font=('Century Schoolbook', 20))
        label.place(x=30, y=20)
        label = ttk.Label(self.root, text="Enter the number of servers: ", font=('Times New Roman', 16))
        label.place(x=30, y=80)
        tb1 = ttk.Entry(self.root, font=('Times New Roman', 13))
        tb1.place(x=300, y=83)
        label = ttk.Label(self.root, text="Enter the number of Clients: ", font=('Times New Roman', 16))
        label.place(x=30, y=130)
        tb2 = ttk.Entry(self.root, font=('Times New Roman', 13))
        tb2.place(x=300, y=133)
        button = tk.Button(self.root, text="Next", font=('Century Gothic', 18),
                           command=lambda: self.simulation(tb1.get(), tb2.get()))
        button.place(x=30, y=200)

    def simulation(self, n, m):
        self.root.destroy()
        Simulate(int(n), int(m))


class Client:
    def __init__(self, port):
        global host
        self.client_socket = s.socket()
        self.client_socket.connect((host, port))


class Server:
    def __init__(self, port_numberr, m):
        global host
        self.server_socket = s.socket()
        self.server_socket.bind((host, port_numberr))
        self.server_socket.listen(m)


class LoadBalancer:
    def __init__(self, n, m):
        self.servers = {}
        self.capacities = [0] * n
        self.clients = {}
        self.server_sockets = deque()
        self.n = n
        self.m = m
        self.connection_timeout = 0.005
        self.counters = [0] * n
        self.events = {}
        self.timers = deque()
        self.threshold = 4
        self.ip_hashes = {}
        self.bandwidth = [0] * n
        self.nlb_logs = []

    def update_capacities(self):
        global port_number
        for i in range(1, self.n + 1):
            self.servers[f"Server{i}"] = deque()
            for k in range(self.capacities[i - 1]):
                self.servers[f"Server{i}"].append(port_number)
                port_number += 1

    def on_closing(self):
        for hehe in self.server_sockets:
            hehe.close()

    def StaticRoundRobin(self):
        self.events = {}

        clients = []
        j = 0
        for i in range(self.n):
            self.capacities[i] = self.m
        self.update_capacities()
        for i in range(self.m):
            aServer = Server(self.servers[f"Server{j + 1}"].popleft(), self.m)
            address, port = aServer.server_socket.getsockname()
            self.server_sockets.append(aServer.server_socket)
            clients.append(Client(port))
            client, addr = aServer.server_socket.accept()
            print(f"Client {addr} just connected to the server{j + 1} represented by {address, port}")
            self.events[f"client{i}"] = (j, port)
            self.nlb_logs.append(
                f"Redirected client {i} request to server {j}")
            j = (j + 1) % self.n


    def ContentAwareLB(self, services, requests):
        global port_number
        self.events = {}
        clients = []
        capacity = self.m
        counters = {}
        for request in requests:
            counters[request] = 0
        for service in services:
            for i in range(self.n):
                self.servers[f"{service}:server{i + 1}"] = deque()
                for j in range(capacity):
                    self.servers[f"{service}:server{i + 1}"].append(port_number)
                    port_number += 1
        i = 0
        for request in requests:
            aServer = Server(self.servers[f"{request}:server{counters[request] + 1}"].popleft(), self.m)
            address, port = aServer.server_socket.getsockname()
            self.server_sockets.append(aServer.server_socket)
            clients.append(Client(port))
            client, addr = aServer.server_socket.accept()
            print(f"Client {addr} just connected to the server{counters[request] + 1} for {request}"
                  f" represented by {address, port}")
            self.events[f"client{i}"] = (f"{request}:server{counters[request] + 1}", port)
            self.nlb_logs.append(
                f"Redirected client {i} request to {request} server number {counters[request]}")
            i += 1
            counters[request] = (counters[request] + 1) % self.n
            client.close()

    def IpHashLoadBalancing(self):
        i = 0
        for j in range(self.n):
            self.capacities[j] = self.m
        self.update_capacities()
        clients = []
        self.events = {}
        j = 0
        random_counting = 0
        while i < self.m:
            if len(self.timers) > 0 and time.time() >= self.timers[0][0] + self.connection_timeout:
                a, b, c, last = self.timers.popleft()
                self.events[last + "Timeout"] = (b, c)
                self.servers[f"Server{b + 1}"].append(c)
                hehe = self.server_sockets.popleft()
                self.nlb_logs.append(
                    f"client {last} Timed out")
                hehe.close()
            if f"client{i}" in self.ip_hashes:
                print(f"IP Hash matched for client {i}: ", self.ip_hashes[f"client{i}"])
                serverNo, port = self.ip_hashes[f"client{i}"]
                print(self.servers[f"Server{serverNo + 1}"])
                self.servers[f"Server{serverNo + 1}"].remove(port)
                aServer = Server(port, self.m)
                address, port = aServer.server_socket.getsockname()
                self.timers.append((time.time(), serverNo, port, f"client{i}"))
                self.server_sockets.append(aServer.server_socket)
                clients.append(Client(port))
                client, addr = aServer.server_socket.accept()
                print(f"Client {addr} just connected to the server{j + 1} represented by {address, port}")
                self.nlb_logs.append(
                    f"Hash found for client {i} , redirected request to server {serverNo}")
                self.events[f"client{i}"] = (j, port)
            else:
                print(f"Else part for client {i}")
                aServer = Server(self.servers[f"Server{j + 1}"].popleft(), self.m)
                address, port = aServer.server_socket.getsockname()
                self.timers.append((time.time(), j, port, f"client{i}"))
                self.server_sockets.append(aServer.server_socket)
                clients.append(Client(port))
                client, addr = aServer.server_socket.accept()
                self.ip_hashes[f"client{i}"] = (j, port)
                print(f"Client {addr} just connected to the server{j + 1} represented by {address, port}")
                self.nlb_logs.append(
                    f"Redirected client {i} request to server {j}")
                self.events[f"client{i}"] = (j, port)
                j = (j + 1) % self.n
            i += 1
        while len(self.timers) > 0:
            if time.time() >= self.timers[0][0]:
                a, b, c, last = self.timers.popleft()
                self.events[last + "Timeout"] = (b, c)
                self.servers[f"Server{b + 1}"].append(c)
                hehe = self.server_sockets.popleft()
                self.nlb_logs.append(
                    f"client {last} Timed out")
                hehe.close()
            self.events[f"NothingHappened{random_counting}"] = True
            random_counting += 1
        print(self.servers)

    def RoundRobin(self):
        clients = []
        self.events = {}
        j = 0
        i = 0
        random_counting = 0
        while i < self.m:
            if len(self.timers) > 0 and time.time() >= self.timers[0][0] + self.connection_timeout:
                a, b, c, last = self.timers.popleft()
                self.events[last + "Timeout"] = (b, c)
                self.servers[f"Server{b + 1}"].append(c)
                hehe = self.server_sockets.popleft()
                self.nlb_logs.append(
                    f"client {last} Timed out")
                hehe.close()
            if len(self.servers[f"Server{j + 1}"]) > 0:
                aServer = Server(self.servers[f"Server{j + 1}"].popleft(), self.m)
                address, port = aServer.server_socket.getsockname()
                self.timers.append((time.time(), j, port, f"client{i}"))
                self.server_sockets.append(aServer.server_socket)
                clients.append(Client(port))
                client, addr = aServer.server_socket.accept()
                print(f"Client {addr} just connected to the server{j + 1} represented by {address, port}")
                self.events[f"client{i}"] = (j, port)
                self.nlb_logs.append(
                    f"Redirected client {i} request to server {j}")
                i += 1
                random_counting += 1
                client.close()
            else:
                self.nlb_logs.append(
                    f"Redirection of client {i} request to server {j} failed (No capacity left)")
                print(f"Queue was found empty for server{j}")
                self.events[f"NothingHappened{random_counting}"] = True
            j = (j + 1) % self.n
        while len(self.timers) > 0:
            if time.time() >= self.timers[0][0]:
                a, b, c, last = self.timers.popleft()
                self.events[last + "Timeout"] = (b, c)
                self.nlb_logs.append(
                    f"client {last} Timed out")
            self.events[f"NothingHappened{random_counting}"] = True
            random_counting += 1

    def Random(self, option):
        if option == "s":
            for i in range(self.n):
                self.capacities[i] = self.m
            self.update_capacities()
        self.events = {}
        clients = []
        j = random.randint(0, self.n - 1)
        for i in range(self.m):
            if len(self.servers[f"Server{j + 1}"]) > 0:
                aServer = Server(self.servers[f"Server{j + 1}"].popleft(), self.m)
                address, port = aServer.server_socket.getsockname()
                self.server_sockets.append(aServer.server_socket)
                clients.append(Client(port))
                client, addr = aServer.server_socket.accept()
                print(f"Client {addr} just connected to the server{j + 1} represented by {address, port}")
                self.events[f"client{i}"] = (j, port)
                self.nlb_logs.append(
                    f"Redirected client {i} request to server {j}")
                if self.capacities[j] - len(self.servers[f"Server{j + 1}"]) >= self.threshold:
                    self.events["ThresholdReached"] = (j + 1, i)
                    print(f"THRESHOLD REACHED for server {j}")
                    if option == "s":
                        self.LeastConnections()
                    else:
                        self.WeightedLeastConnections()
                    break
            else:
                self.nlb_logs.append(
                    f"Redirection of client {i} request to server {j} failed (No capacity left)")
            j = random.randint(0, self.n - 1)

    def LeastConnections(self):
        q = queue.PriorityQueue()
        Sum = 0
        for i in range(self.n):
            temp = self.capacities[i] - len(self.servers[f"Server{i + 1}"])
            q.put((temp, i))
            Sum += temp
        while Sum < self.m:
            print(Sum)
            _, server_number = q.get()
            if len(self.servers[f"Server{server_number + 1}"]) > 0:
                aServer = Server(self.servers[f"Server{server_number + 1}"].popleft(), self.m)
                address, port = aServer.server_socket.getsockname()
                self.server_sockets.append(aServer.server_socket)
                Client(port)
                client, addr = aServer.server_socket.accept()
                print(f"Client {addr} just connected to the server{server_number + 1} represented by {address, port}")
                self.events[f"client{Sum}"] = (server_number, port)
                self.nlb_logs.append(
                    f"Redirected client {Sum} request to server {server_number}")
                Sum += 1
                q.put((_ + 1, server_number))
            else:
                self.nlb_logs.append(
                    f"Redirection of client {Sum} request to server {server_number} failed (No capacity left)")



    def WeightedLeastConnections(self):
        q = queue.PriorityQueue()
        Sum = 0
        random_counting = 0
        print("Printing the capacities")
        for i in range(self.n):
            temp = self.capacities[i] - len(self.servers[f"Server{i + 1}"])
            print(temp)
            q.put((-1 * (self.capacities[i] - temp), i))
            Sum += temp
        while Sum < self.m:
            _, server_number = q.get()
            temp = self.capacities[server_number] - len(self.servers[f"Server{server_number + 1}"])
            print(_, server_number)
            if len(self.servers[f"Server{server_number + 1}"]) > 0:
                aServer = Server(self.servers[f"Server{server_number + 1}"].popleft(), self.m)
                address, port = aServer.server_socket.getsockname()
                self.server_sockets.append(aServer.server_socket)
                Client(port)
                client, addr = aServer.server_socket.accept()
                print(f"Client {addr} just connected to the server{server_number + 1} represented by {address, port}")
                self.events[f"client{Sum}"] = (server_number, port)
                self.nlb_logs.append(
                    f"Redirected client {Sum} request to server {server_number}")
                Sum += 1
                q.put((-1 * (self.capacities[server_number] - temp-1), server_number))
            else:
                self.nlb_logs.append(
                    f"Redirection of client {Sum} request to server {server_number} failed (No capacity left)")


class Simulate:
    def __init__(self, n, m):
        self.root = tk.Tk()
        self.result_var = tk.BooleanVar(self.root)
        self.simulation_speed =1000 # Change this so that program runs faster/slower.
        self.screenwidth = 1500
        self.screenheight = 1000
        self.colors = [
            "red",  # Red color
            "green",  # Green color
            "blue",  # Blue color
            "cyan",  # Cyan color
            "magenta",  # Magenta color
            "yellow",  # Yellow color
            "orange",  # Orange color
            "purple",  # Purple color
            "pink",  # Pink color
            "brown",  # Brown color
            "white",  # White color
            "lightblue",  # Light blue color
            "lightgreen"  # Light green color
        ]
        self.lb = LoadBalancer(n, m)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.n, self.m = n, m
        self.current_window = "basic info"
        self.selected_option = []
        self.root.withdraw()
        self.coordinates = {}
        self.events_labels = (1000, 30)
        self.nlb_icon = tk.PhotoImage(file="nlb-icon.png")
        self.server_icon = tk.PhotoImage(file="server-icon.png")
        self.pc_icon = tk.PhotoImage(file="pc.png")
        self.pc_icon_height = 40
        self.serverImages = []
        self.serverLabels = []
        self.DisplayMenu()
    def accelerate(self):
        self.simulation_speed -= 250
    def brake(self):
        self.simulation_speed += 250
    def DisplayMenu(self):
        self.root.deiconify()
        self.root.geometry(f"{self.screenwidth}x{self.screenheight}")
        self.root.title("Main Menu")
        self.root.configure(bg="Black")
        style = ttk.Style()
        style.configure("TLabel", background="black", foreground="white")
        label = ttk.Label(self.root, text="Select an algorithm to run:", font=('Times New Roman', 20))
        label.place(x=30, y=30)
        srr_btn = tk.Button(self.root, text="Static Round Robin", font=('Century Gothic', 18), command=self.SRR)
        srr_btn.place(x=30, y=100)
        srr_btn.config(width=28)
        btn = tk.Button(self.root, text="Least Connection", font=('Century Gothic', 18),command=self.SLC)
        btn.place(x=30, y=200)
        btn.config(width=28)
        btn = tk.Button(self.root, text="Weighted Least Connection", font=('Century Gothic', 18), command=self.DLC)
        btn.place(x=30, y=300)
        btn.config(width=28)
        btn = tk.Button(self.root, text="IP Hash Load balancing", font=('Century Gothic', 18), command=self.IPH)
        btn.place(x=30, y=400)
        btn.config(width=28)
        btn = tk.Button(self.root, text="Content-Aware Load Balancing", font=('Century Gothic', 18), command=self.CA)
        btn.place(x=30, y=500)
        btn.config(width=28)
        self.root.mainloop()

    def CA(self):
        self.Run("ContentAware")

    def IPH(self):
        self.Run("iphash")

    def DLC(self):
        self.Run("weighted least connections")

    def SLC(self):
        self.Run("least connections")

    def SRR(self):
        self.Run("static round robin")

    def on_closing(self):
        if self.lb:
            self.lb.on_closing()
        self.root.destroy()
        MainMenu()

    def proceed(self):
        self.result_var.set(True)

    def initialize_pcs(self, canvas):
        pc_icon_height = min(math.floor((self.screenheight - 40 - 14 * self.m) / self.m), 30)
        space_between = 14 + pc_icon_height
        current = (90, 30)
        for i in range(self.m):
            label = tk.Label(canvas, text=f"Client {i + 1}")
            canvas.create_window(current[0] - 60, current[1], window=label)

            self.coordinates[f"client{i}"] = (current[0] + 20, current[1])
            current = (current[0], current[1] + space_between)
        label = tk.Label(canvas, text="Network load balancer")
        canvas.create_window(500, 680, window=label)
        self.coordinates["nlb"] = (500, 600)

    def initialize_canvas(self):
        self.root.deiconify()
        self.root.geometry(f"{self.screenwidth}x{self.screenheight}")
        self.root.title("Simulation window")
        self.root.configure(bg="white")
        canvas = tk.Canvas(self.root, bg="black", width=1500, height=800)
        self.coordinates = {}
        self.initialize_pcs(canvas)
        offset = (0, 0)
        starting_location = (800, 70)
        for i in range(self.n):
            label = tk.Label(canvas, text=f"Server {i + 1}")
            self.serverLabels.append(
                canvas.create_window(starting_location[0] + 70, starting_location[1] + offset[1], window=label))
            self.coordinates[f"server{i}"] = (
                starting_location[0] + offset[0] - 20, starting_location[1] + offset[1] - 20)
            offset = (offset[0], offset[1] + 150)
        label = ttk.Label(canvas, text="NLB Logs")
        label.place(x=1200, y=10)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return canvas

    def add_images(self, canvas):
        space_between = 14 + self.pc_icon_height
        current = (90, 30)
        for i in range(self.m):
            canvas.create_image(current[0], current[1], image=self.pc_icon)
            current = (current[0], current[1] + space_between)
        canvas.create_image(500, 600, image=self.nlb_icon)
        offset = (0, 0)
        starting_location = (800, 70)
        for i in range(self.n):
            self.serverImages.append(
                canvas.create_image(starting_location[0] + offset[0], starting_location[1] + offset[1],
                                    image=self.server_icon))
            offset = (offset[0], offset[1] + 150)

    def RunStaticRoundRobin(self, canvas):

        label = ttk.Label(canvas, text="", wraplength=250, justify="left")
        label.place(x=1150, y=30)
        ff_img = tk.PhotoImage(file='fast-forward.png')
        slow_img = tk.PhotoImage(file='fast-rewind.png')
        ff_img = resize_image(ff_img, 30, 30)
        slow_img = resize_image(slow_img, 30, 30)
        ff_btn = tk.Button(self.root, image=ff_img, command=self.accelerate)
        slow_btn = tk.Button(self.root, image=slow_img, command=self.brake)
        ff_btn.place(x=1150, y=700)
        slow_btn.place(x=1100, y=700)
        i = 0
        for key, value in self.lb.events.items():

            line1 = canvas.create_line(self.coordinates[key][0], self.coordinates[key][1],
                                       self.coordinates["nlb"][0] - 40, self.coordinates["nlb"][1], width=2,
                                       fill=self.colors[i % len(self.colors)])
            self.result_var.set(False)
            self.root.after(self.simulation_speed, self.proceed)
            self.root.wait_variable(self.result_var)

            line2 = canvas.create_line(
                self.coordinates["nlb"][0] + 40, self.coordinates["nlb"][1],
                self.coordinates[f"server{value[0]}"][0],
                self.coordinates[f"server{value[0]}"][1],
                width=2, fill=self.colors[i % len(self.colors)])

            self.result_var.set(False)
            self.root.after(self.simulation_speed, self.proceed)
            self.root.wait_variable(self.result_var)
            canvas.delete(line1)
            canvas.delete(line2)
            line = canvas.create_line(self.coordinates[key][0],
                                      self.coordinates[key][1],
                                      self.coordinates[f"server{value[0]}"][0],
                                      self.coordinates[f"server{value[0]}"][1],
                                      width=2,
                                      fill=self.colors[i % len(self.colors)])
            i += 1
            if len(self.lb.nlb_logs) > 0:
                item = self.lb.nlb_logs.pop(0)
                label.config(text=label.cget("text") + "\n" + item)
        while len(self.lb.nlb_logs) > 0:
            item = self.lb.nlb_logs.pop(0)
            label.config(text=label.cget("text") + "\n" + item)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


    def get_capacities(self, canvas, flag=False):
        offset = (0, 0)
        starting_location = (850, 60)
        label = ttk.Label(self.root)
        label.place(x=920,y=20)
        if flag:
            label.config(text="Capacity,Bandwidth")
        else:
            label.config(text="Capacity")
        tbs = []
        for i in range(self.n):
            combo = tk.Entry(self.root)
            combo.place(x=starting_location[0] + 70, y=starting_location[1] + offset[1])
            offset = (offset[0], offset[1] + 150)
            tbs.append(combo)
        hehe = tk.PhotoImage(file="play.png")
        hehe = resize_image(hehe,50,50)
        btn = tk.Button(self.root, image=hehe, width=50, height=50,bg="black", borderwidth=0, text="Simulate", command=self.proceed)
        canvas.create_window(1450, 30, window=btn)
        self.result_var.set(False)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.root.wait_variable(self.result_var)
        for i in range(self.n):
            if flag:
                hehe = tbs[i].get()
                capacity_str, bandwidth_str = hehe.split(',')
                self.lb.capacities[i] = int(capacity_str)
                self.lb.bandwidth[i] = int(bandwidth_str)
            else:
                self.lb.capacities[i] = int(tbs[i].get())
        self.lb.update_capacities()
        for widget in tbs:
            widget.destroy()
        offset = (0, 0)
        starting_location = (870, 70)
        for i in range(self.n):
            combo = ttk.Label(canvas, text=f"Capacity: {self.lb.capacities[i]}")
            canvas.create_window(starting_location[0] + 70, starting_location[1] + offset[1], window=combo)
            if flag:
                combo = ttk.Label(canvas, text=f"Bandwidth: {self.lb.bandwidth[i]}")
                canvas.create_window(starting_location[0] + 170, starting_location[1] + offset[1], window=combo)
            offset = (offset[0], offset[1] + 150)
    def displayLine(self,label):
        item = self.lb.nlb_logs.pop(0)
        label.config(text=label.cget("text") + "\n" + item)

    def RunDynamicRoundRobin(self, canvas, option=None):
        label = ttk.Label(canvas, text="", wraplength=250, justify="left")
        label.place(x=1150, y=30)
        lines = {}
        i = 0
        pattern = r'client(\d+)Timeout'
        pattern2 = r'NothingHappened(\d+)'

        for key, value in self.lb.events.items():
            match = re.match(pattern, key)
            match2 = re.match(pattern2, key)
            if match:
                self.result_var.set(False)
                self.root.after(self.simulation_speed + 300, self.proceed)
                self.root.wait_variable(self.result_var)
                print(key)
                line_key = key.split("Timeout")[0]
                canvas.delete(lines[f"{line_key} -> server{value[0]}"])
            elif match2:
                self.result_var.set(False)
                self.root.after(self.simulation_speed + 300, self.proceed)
                self.root.wait_variable(self.result_var)
            elif key != "ThresholdReached":
                line1 = canvas.create_line(self.coordinates[key][0], self.coordinates[key][1],
                                           self.coordinates["nlb"][0] - 40, self.coordinates["nlb"][1], width=2,
                                           fill=self.colors[i % len(self.colors)])
                self.result_var.set(False)
                self.root.after(self.simulation_speed, self.proceed)
                self.root.wait_variable(self.result_var)

                line2 = canvas.create_line(
                    self.coordinates["nlb"][0] + 40, self.coordinates["nlb"][1],
                    self.coordinates[f"server{value[0]}"][0],
                    self.coordinates[f"server{value[0]}"][1],
                    width=2, fill=self.colors[i % len(self.colors)])
                self.result_var.set(False)
                self.root.after(self.simulation_speed, self.proceed)
                self.root.wait_variable(self.result_var)
                canvas.delete(line1)
                canvas.delete(line2)
                lines[f"{key} -> server{value[0]}"] = canvas.create_line(self.coordinates[key][0],
                                                                         self.coordinates[key][1],
                                                                         self.coordinates[f"server{value[0]}"][0],
                                                                         self.coordinates[f"server{value[0]}"][1],
                                                                         width=2,
                                                                         fill=self.colors[i % len(self.colors)])
            if len(self.lb.nlb_logs) > 0:
                self.displayLine(label)
            i += 1
        while len(self.lb.nlb_logs) > 0:
            self.displayLine(label)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if option:
            return
        self.root.mainloop()

    def update_space(self, capacities):
        inc = 70
        for i in range(self.n):
            label = ttk.Label(self.root, text=f"Server {i}: {capacities[i]}")
            label.place(x=self.coordinates["nlb"][0], y=self.coordinates["nlb"][1] + 30 + inc)
            inc += 25

    def LeastConnections(self, canvas):
        i = 0
        label = ttk.Label(canvas, text="", wraplength=250, justify="left")
        label.place(x=1150, y=30)
        ff_img = tk.PhotoImage(file='fast-forward.png')
        slow_img = tk.PhotoImage(file='fast-rewind.png')
        ff_img = resize_image(ff_img, 30, 30)
        slow_img = resize_image(slow_img, 30, 30)
        ff_btn = tk.Button(self.root, image=ff_img, command=self.accelerate)
        slow_btn = tk.Button(self.root, image=slow_img, command=self.brake)
        ff_btn.place(x=1150, y=700)
        slow_btn.place(x=1100, y=700)
        capacities = [capacity for capacity in self.lb.capacities]
        window_label = tk.Label(self.root, text="Randomly assigning clients", font=("Helvetica", 15))
        canvas.create_window(500, 10, window=window_label)
        for key, value in self.lb.events.items():
            self.update_space(capacities)

            if key == "ThresholdReached":
                messagebox.showinfo(title="Threshold reached alert",
                                    message=f"Maximum threshold reached for server {value[0]},"
                                            "switching to Least Connections algorithm")
                window_label.config(text="Least Connections Algorithm")

            else:
                capacities[value[0]] -= 1
                line1 = canvas.create_line(self.coordinates[key][0], self.coordinates[key][1],
                                           self.coordinates["nlb"][0] - 40, self.coordinates["nlb"][1], width=2,
                                           fill=self.colors[i % len(self.colors)])
                self.result_var.set(False)
                self.root.after(self.simulation_speed, self.proceed)
                self.root.wait_variable(self.result_var)

                line2 = canvas.create_line(
                    self.coordinates["nlb"][0] + 40, self.coordinates["nlb"][1],
                    self.coordinates[f"server{value[0]}"][0],
                    self.coordinates[f"server{value[0]}"][1],
                    width=2, fill=self.colors[i % len(self.colors)])

                self.result_var.set(False)
                self.root.after(self.simulation_speed, self.proceed)
                self.root.wait_variable(self.result_var)
                canvas.delete(line1)
                canvas.delete(line2)
                line = canvas.create_line(self.coordinates[key][0],
                                          self.coordinates[key][1],
                                          self.coordinates[f"server{value[0]}"][0],
                                          self.coordinates[f"server{value[0]}"][1],
                                          width=2,
                                          fill=self.colors[i % len(self.colors)])
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            i += 1
            if len(self.lb.nlb_logs) > 0:
                self.displayLine(label)
        while len(self.lb.nlb_logs) > 0:
            self.displayLine(label)
        self.root.mainloop()

    def MapHashedClient(self, key, hashed_server, port, canvas):
        i = 0
        line1 = canvas.create_line(self.coordinates[key][0], self.coordinates[key][1],
                                   self.coordinates["nlb"][0] - 40, self.coordinates["nlb"][1], width=2,
                                   fill=self.colors[i % len(self.colors)])
        self.result_var.set(False)
        self.root.after(self.simulation_speed, self.proceed)
        self.root.wait_variable(self.result_var)

        line2 = canvas.create_line(
            self.coordinates["nlb"][0] + 40, self.coordinates["nlb"][1],
            self.coordinates[f"server{hashed_server}"][0],
            self.coordinates[f"server{hashed_server}"][1],
            width=2, fill=self.colors[i % len(self.colors)])
        self.result_var.set(False)
        self.root.after(self.simulation_speed, self.proceed)
        self.root.wait_variable(self.result_var)
        canvas.delete(line1)
        canvas.delete(line2)
        aline = canvas.create_line(self.coordinates[key][0],
                                   self.coordinates[key][1],
                                   self.coordinates[f"server{hashed_server}"][0],
                                   self.coordinates[f"server{hashed_server}"][1],
                                   width=2,
                                   fill=self.colors[i % len(self.colors)])

        return aline

    def further_connections(self, canvas):
        label = ttk.Label(canvas, text="", wraplength=250, justify="left")
        label.place(x=1150, y=30)
        self.RunDynamicRoundRobin(canvas, True)
        self.lb.events = {}
        label = tk.Label(self.root, text="Send request for client number: ", font=('Times New Roman', 15))
        label.place(x=200, y=400)
        tb1 = tk.Entry(self.root, width=5, font=('Times New Roman', 13))
        tb1.place(x=500, y=400)
        btn = tk.Button(self.root, text="Send request", command=self.proceed)
        btn.place(x=230, y=500)
        self.result_var.set(False)
        self.root.wait_variable(self.result_var)
        self.lb.m = 1
        key = f"client{int(tb1.get()) - 1}"
        hashed_server, port = self.lb.ip_hashes[key]
        aline = self.MapHashedClient(key, hashed_server, port, canvas)
        print("Hash found in the NLB, mapping client request to server ", hashed_server)
        self.result_var.set(False)
        self.root.after(500, self.proceed)
        self.root.wait_variable(self.result_var)
        canvas.delete(aline)
        if len(self.lb.nlb_logs) > 0:
            self.displayLine(label)
        self.events_labels = (self.events_labels[0], self.events_labels[1] + 30)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def ContentAware(self, canvas, tbs):
        services = set()
        requests = []
        for i in range(self.m):
            services.add(tbs[i].get())
            requests.append(tbs[i].get())
        for entry_box in tbs:
            entry_box.destroy()
        for i in range(self.m):
            label = ttk.Label(self.root,text=requests[i])
            label.place(x=self.coordinates[f"client{i}"][0] + 20, y=self.coordinates[f"client{i}"][1]-10)
        ff_img = tk.PhotoImage(file='fast-forward.png')
        slow_img = tk.PhotoImage(file='fast-rewind.png')
        ff_img = resize_image(ff_img, 30, 30)
        slow_img = resize_image(slow_img, 30, 30)
        ff_btn = tk.Button(self.root, image=ff_img, command=self.accelerate)
        slow_btn = tk.Button(self.root, image=slow_img, command=self.brake)
        ff_btn.place(x=1200, y=700)
        slow_btn.place(x=1150, y=700)
        curr = (800, 120)
        curr_servers = (930, 50)
        client_info = {}
        icon_references = []  # Store references to the PhotoImage objects
        for service in services:
            icon = tk.PhotoImage(file=f"{service}.png")
            icon = resize_image(icon, 120, 100)
            icon_references.append(icon)  # Store the reference to the PhotoImage object
            canvas.create_image(curr[0], curr[1], image=icon)
            label = ttk.Label(self.root,text=service)
            label.place(x=curr[0]-20,y=curr[1]+60)
            for j in range(self.n):
                server_icon = resize_image(self.server_icon, 50, 50)
                canvas.create_image(curr_servers[0], curr_servers[1], image=server_icon)
                icon_references.append(server_icon)
                label = ttk.Label(self.root, text=f"Server {j+1}")
                label.place(x=curr_servers[0]+30,y=curr_servers[1])
                print(f"{service}:server{j+1}")
                self.coordinates[f"{service}:server{j+1}"] = (curr[0] - 60, curr[1] + 5)
                client_info[f"{service}:server{j+1}"] = ttk.Label(self.root,text=":")
                client_info[f"{service}:server{j+1}"].place(x=curr_servers[0]+80,y=curr_servers[1])
                curr_servers = (curr_servers[0], curr_servers[1] + 90)
            curr = (curr[0], curr[1] + 170)
            curr_servers = (curr_servers[0], curr_servers[1] + 20)
        self.lb.ContentAwareLB(services, requests)
        label = ttk.Label(canvas, text="", wraplength=250, justify="left")
        label.place(x=1150, y=30)
        i = 0
        for key, value in self.lb.events.items():
            line1 = canvas.create_line(self.coordinates[key][0], self.coordinates[key][1],
                                       self.coordinates["nlb"][0] - 40, self.coordinates["nlb"][1], width=2,
                                       fill=self.colors[i % len(self.colors)])
            self.result_var.set(False)
            self.root.after(self.simulation_speed, self.proceed)
            self.root.wait_variable(self.result_var)
            client_info[value[0]].config(text = client_info[value[0]].cget("text") + "," + key)
            line2 = canvas.create_line(
                self.coordinates["nlb"][0] + 40, self.coordinates["nlb"][1],
                self.coordinates[value[0]][0],
                self.coordinates[value[0]][1],
                width=2, fill=self.colors[i % len(self.colors)])

            self.result_var.set(False)
            self.root.after(self.simulation_speed, self.proceed)
            self.root.wait_variable(self.result_var)
            canvas.delete(line1)
            canvas.delete(line2)
            line = canvas.create_line(self.coordinates[key][0],
                                      self.coordinates[key][1],
                                      self.coordinates[value[0]][0],
                                      self.coordinates[value[0]][1],
                                      width=2,
                                      fill=self.colors[i % len(self.colors)])
            i += 1
            if len(self.lb.nlb_logs) > 0:
                self.displayLine(label)
        while len(self.lb.nlb_logs) > 0:
            self.displayLine(label)
        self.root.mainloop()

    def getScenario(self, canvas):
        self.root.withdraw()
        self.root.deiconify()
        self.root.geometry(f"{self.screenwidth}x{self.screenheight}")
        tbs = []
        for i in range(self.m):
            tb = ttk.Entry(self.root)
            tb.place(x=self.coordinates[f"client{i}"][0] + 50, y=self.coordinates[f"client{i}"][1] - 10)
            tbs.append(tb)
        for i in range(self.n):
            canvas.delete(self.serverImages[i])
            canvas.delete(self.serverLabels[i])
        # Keep a reference to the photo image object
        self.hehe = tk.PhotoImage(file="play.png")
        self.hehe = resize_image(self.hehe, 50, 50)
        btn = tk.Button(self.root, image=self.hehe, width=50, height=50, bg="black", borderwidth=0, text="Simulate",
                        command=lambda: self.ContentAware(canvas, tbs))
        canvas.create_window(1450,30,window=btn)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def Run(self, option):
        canvas = self.initialize_canvas()
        self.pc_icon_height = min(math.floor((self.screenheight - 40 - 14 * self.m) / self.m), 30)
        self.nlb_icon = resize_image(self.nlb_icon, 80, 80)
        self.server_icon = resize_image(self.server_icon, 100, 100)
        self.pc_icon = resize_image(self.pc_icon, 50, self.pc_icon_height)
        self.add_images(canvas)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if option == "least connections":
            self.lb.Random("s")
            self.LeastConnections(canvas)
        elif option == "static round robin":
            self.lb.StaticRoundRobin()
            self.RunStaticRoundRobin(canvas)
        elif option == "weighted least connections":
            self.get_capacities(canvas)
            self.lb.Random("d")
            self.LeastConnections(canvas)
        elif option == "ContentAware":
            self.getScenario(canvas)
        elif option == "iphash":
            self.lb.IpHashLoadBalancing()
            print(self.lb.events)
            while True:
                self.further_connections(canvas)


MainMenu()
'''
start_time = time.time()
end_time = time.time()
    with open('execution_times.txt', 'a') as file:
        file.write(f"Ip Hash Load Balancing: {self.n}, {self.m}, {end_time - start_time}\n")
'''