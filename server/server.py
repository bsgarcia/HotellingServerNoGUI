import json
import socketserver
from multiprocessing import Queue, Event
from threading import Thread

from utils.utils import log


class TCPHandler(socketserver.StreamRequestHandler):

    name = "ThreadedTCPRequestHandler"

    def handle(self):

        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        data = self.rfile.readline().strip()

        if self.server.running_game.is_set() and data:

            try:

                data = data.decode()
                self.server.manager_queue.put(("server", "request", data))
                manager_response = self.server.server_queue.get()

                if manager_response[0] == "reply":
                    response = manager_response[1]

                else:
                    response = "Probably no game is running or trying to shutting down."

            except Exception:
                response = "Problem with handling request '{}'.". format(data)

        else:
            response = "No game is running and/or request is empty."

        log("Reply '{}' to '{}'.".format(response, data), self.name)

        # Likewise, self.wfile is a file-like object used to write back to the client
        self.wfile.write(response.encode())


class TCPGamingServer(socketserver.TCPServer):

    def __init__(self, server_address, running_game, manager_queue, server_queue):
        self.running_game = running_game
        self.server_queue = server_queue
        self.manager_queue = manager_queue
        super().__init__(server_address, TCPHandler)


class ServerManager(Thread):

    name = "Server"

    with open("parameters/network.json") as file:
        param = json.load(file)

    def __init__(self, manager_queue, server_queue, running_game):

        Thread.__init__(self)

        self.manager_queue = manager_queue
        self.server_queue = server_queue
        self.running_game = running_game

        self.shutdown_event = Event()
        self.tcp_server = None

    def run(self):

        while not self.shutdown_event.is_set():

            msg = self.server_queue.get()
            log("I received msg '{}'.".format(msg), self.name)
            if msg and msg[0] == "Go":
                try:

                    local = msg[1]
                    if local:
                        ip_address = "localhost"

                    else:
                        ip_address = self.param["ip_address"]

                    log("Try to connect...", self.name)
                    self.tcp_server = TCPGamingServer(
                        server_address=(ip_address, self.param["port"]),
                        running_game=self.running_game,
                        manager_queue=self.manager_queue,
                        server_queue=self.server_queue
                    )
                    self.manager_queue.put(("server", "running"))
                    self.tcp_server.serve_forever()

                except Exception as e:
                    log("Error: {}".format(e), self.name)
                    self.manager_queue.put(("server", "error"))

                finally:
                    log("Close server...", name=self.name)
                    self.shutdown()
                    log("Server closed.", self.name)

        log("I'm dead.", self.name)

    def shutdown(self):

        if self.tcp_server is not None:
            self.tcp_server.shutdown()
            self.tcp_server.server_close()

    def end(self):

        self.shutdown_event.set()

def main():

    server_queue = Queue()
    manager_queue = Queue(),

    s = ServerManager(manager_queue, server_queue)
    s.start()

    server_queue.put(("Go", 1))


if __name__ == "__main__":

    main()