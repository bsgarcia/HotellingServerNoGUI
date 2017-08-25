import socketserver
import http.server
from multiprocessing import Queue, Event
from threading import Thread
import time 

from utils.utils import Logger, get_local_ip


class HttpHandler(http.server.SimpleHTTPRequestHandler, Logger):

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
            self.server.parent.check_client_connection(self.client_address[0], response)
        except Exception as err:
            self.log("Error during connection checking: {}".format(err))

        self.log("Reply '{}' to '{}'.".format(response, data))

        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(response.encode())

        def log_message(self, *args):
            return


class TCPGamingServer(Logger, socketserver.TCPServer):

    def __init__(self, parent, server_address, cont, controller_queue, server_queue):
        self.allow_reuse_address = True
        self.server_queue = server_queue
        self.cont = cont
        self.controller_queue = controller_queue
        self.parent = parent

        super().__init__(server_address, HttpHandler)  # TCPHandler)


class Server(Thread, Logger):

    name = "Server"

    def __init__(self, controller):

        Thread.__init__(self)

        self.cont = controller
        self.param = self.cont.get_parameters("network")

        self.controller_queue = self.cont.queue
        self.queue = Queue()

        self.clients = {}

        self.shutdown_event = Event()
        self.tcp_server = None

        self.timer = Timer(1, self.check_all_client_time_since_last_request)
        self.timer.start()

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
                        parent=self,
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
        self.timer.stop()
        self.shutdown_event.set()
        self.queue.put("break")

    def check_client_connection(self, ip, response):

        if ip not in self.clients.keys():
            self.clients[ip] = {}
            self.clients[ip]["time"] = time.time()
            self.clients[ip]["game_id"] = int(response.split("/")[2])
        else:
            self.clients[ip]["time"] = time.time()

    def check_all_client_time_since_last_request(self):

        for client_ip in self.clients.keys():

            client_time = self.clients[client_ip]["time"]
            time_now = time.time()
            time_since_last_request = int(time_now - client_time)

            self.update_client_time_on_interface(ip=client_ip, time=time_since_last_request)

    def update_client_time_on_interface(self, ip, time):

        game_id = self.clients[ip]["game_id"]
        role = self.cont.data.roles[game_id]
        
        if role:
            if role == "customer":
                if game_id in self.cont.data.customers_id.keys():
                    role_id = self.cont.data.customers_id[game_id]
                    self.update_time(role, role_id, time)
            else:
                if game_id in self.cont.data.firms_id.keys():
                    role_id = self.cont.data.firms_id[game_id]
                    self.update_time(role, role_id, time)

    def update_time(self, role, role_id, time):
        self.cont.data.current_state["connected_{}s".format(role)][role_id] = str(time)


class Timer(Thread):
    def __init__(self, wait, func):
        super().__init__()
        self.func = func
        self.wait = wait
        self._stop_event = False

    def run(self):

        while not self.stopped():
            self.func()
            Event().wait(self.wait)

    def stop(self):
        self._stop_event = True

    def stopped(self):
        return self._stop_event

