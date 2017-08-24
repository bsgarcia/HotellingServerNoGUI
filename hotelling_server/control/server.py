import socketserver
import http.server
from multiprocessing import Queue, Event
from threading import Thread, Timer
import time 

from utils.utils import Logger, get_local_ip


class HttpHandler(http.server.SimpleHTTPRequestHandler, Logger):

    clients = {}
    time_to_be_considered_deconnected = 30

    def do_GET(self):

        data = self.path
        
        if data:

            try:
                self.server.controller_queue.put(("server_request", data))
                controller_response = self.server.server_queue.get()

                if controller_response[0] == "reply":
                    response = controller_response[1]

                else:
                    response = "Probably no game is running or trying to shutting down."

            except Exception as e:
                response = "Server encountered an exception handling request '{}': '''{}'''.". format(data, e)

        else:
            response = "Request is empty."

        try:
            self.check_client_connection(self.client_address[0], response)
            self.check_all_client_time_since_last_request()
        except:
            self.log("Error during connection checking")

        self.log("Reply '{}' to '{}'.".format(response, data))

        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(response.encode())
    
    def check_client_connection(self, ip, response):
        
        if ip not in self.clients.keys():
            self.clients[ip] = {}
            self.clients[ip]["time"] = time.time()
            self.clients[ip]["game_id"] = int(response.split("/")[2])
            self.clients[ip]["connected"] = True
            self.switch_client_status_on_interface(ip=ip, disconnect=False)

        if "reply_init" in response:
            self.clients[ip]["game_id"] = int(response.split("/")[2])

        if ip in self.clients.keys() and not self.clients[ip]["connected"]:
            self.clients[ip]["connected"] = True
            self.clients[ip]["time"] = time.time()
            self.switch_client_status_on_interface(ip=ip, disconnect=False)

    def check_all_client_time_since_last_request(self):
        for client_ip in self.clients.keys():
            if self.clients[client_ip]["connected"]:
                client_time = self.clients[client_ip]["time"]
                time_now = time.time()
                time_since_last_request = int(time_now - client_time)

                if time_since_last_request > self.time_to_be_considered_deconnected:
                    self.switch_client_status_on_interface(ip=client_ip, disconnect=True)

    def switch_client_status_on_interface(self, ip, disconnect):
        game_id = self.clients[ip]["game_id"]
        role = self.server.cont.data.roles[game_id]

        if role == "customer":
            role_id = self.server.cont.data.customers_id[game_id]
        else:
            role_id = self.server.cont.data.firms_id[game_id]

        if disconnect:
            self.clients[ip]["connected"] = False
            self.server.cont.data.current_state["connected_{}s".format(role)][role_id] = ""
        else:
            self.clients[ip]["connected"] = True
            self.server.cont.data.current_state["connected_{}s".format(role)][role_id] = " ✔ "

    def log_message(self, *args):
        return


class TCPGamingServer(Logger, socketserver.TCPServer):

    def __init__(self, server_address, cont, controller_queue, server_queue):
        self.allow_reuse_address = True
        self.server_queue = server_queue
        self.cont = cont
        self.controller_queue = controller_queue
        super().__init__(server_address, HttpHandler)  # TCPHandler)


class Server(Thread, Logger):

    name = "Server"

    def __init__(self, controller):

        Thread.__init__(self)

        self.cont = controller
        self.param = self.cont.get_parameters("network")

        self.controller_queue = self.cont.queue
        self.queue = Queue()

        self.shutdown_event = Event()
        self.tcp_server = None

    def run(self):

        while not self.shutdown_event.is_set():

            self.log("Waiting for a message...")
            msg = self.queue.get()
            self.log("I received msg '{}'.".format(msg))
            if msg and msg[0] == "Go":
                try:

                    if self.param["local"]:
                        ip_address = "localhost"

                    elif self.param["ip_autodetect"]:
                        ip_address = get_local_ip()
                    else:
                        ip_address = self.param["ip_address"]

                    self.log("Try to connect using ip {}...".format(ip_address))
                    self.tcp_server = TCPGamingServer(
                        server_address=(ip_address, self.param["port"]),
                        cont=self.cont,
                        controller_queue=self.controller_queue,
                        server_queue=self.queue
                    )
                    self.controller_queue.put(("server_running", ))

                    self.tcp_server.serve_forever()

                except Exception as e:
                    self.log("Error: {}".format(e))
                    self.controller_queue.put(("server_error", str(e)))

                finally:
                    self.log("Close server...")
                    self.shutdown()
                    self.log("Server closed.")

        self.log("I'm dead.")

    def shutdown(self):

        if self.tcp_server is not None:
            self.tcp_server.shutdown()
            self.tcp_server.server_close()

    def end(self):

        self.shutdown_event.set()
        self.queue.put("break")
