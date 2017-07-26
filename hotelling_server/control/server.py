import socketserver
import http.server
from multiprocessing import Queue, Event
from threading import Thread
from sys import getsizeof

from utils.utils import Logger


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

        self.log("Reply '{}' to '{}'.".format(response, data))

        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(response.encode())

    def log_message(self, *args):
        return


class TCPGamingServer(socketserver.TCPServer):

    def __init__(self, server_address, controller_queue, server_queue):
        self.allow_reuse_address = True
        self.server_queue = server_queue
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

                    else:
                        ip_address = self.param["ip_address"]

                    self.log("Try to connect...")
                    self.tcp_server = TCPGamingServer(
                        server_address=(ip_address, self.param["port"]),
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
