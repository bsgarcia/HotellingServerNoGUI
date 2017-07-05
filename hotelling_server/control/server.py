import socketserver
from multiprocessing import Queue, Event
from threading import Thread

from utils.utils import Logger


class TCPHandler(socketserver.StreamRequestHandler, Logger):

    name = "ThreadedTCPRequestHandler"

    def handle(self):

        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        data = self.rfile.readline().strip()

        if data:

            try:

                data = data.decode()
                self.server.controller_queue.put(("server_request", data))
                controller_response = self.server.server_queue.get()

                if controller_response[0] == "reply":
                    response = controller_response[1]

                else:
                    response = "Probably no game is running or trying to shutting down."

            except Exception as e:
                response = "Problem with handling request '{}': {}". format(data, e)

        else:
            response = "No game is running and/or request is empty."

        self.log("Reply '{}' to '{}'.".format(response, data))

        # Likewise, self.wfile is a file-like object used to write back to the client
        self.wfile.write(response.encode())


class TCPGamingServer(socketserver.TCPServer):

    def __init__(self, server_address, controller_queue, server_queue):
        self.server_queue = server_queue
        self.controller_queue = controller_queue
        super().__init__(server_address, TCPHandler)


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
                    self.controller_queue.put(("server_error", ))

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
