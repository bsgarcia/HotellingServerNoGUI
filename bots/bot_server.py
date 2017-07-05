import socketserver
from multiprocessing import Queue, Event
from threading import Thread

from utils.utils import Logger

from hotelling_server.control import server


class BotController(Logger):

    name = "BotController"

    def __init__(self):

        self.queue = Queue()
        self.server = server.Server(controller=self)
        self.game = BotGame(controller=self)

        self.shutdown = Event()

    def run(self):

        self.server.start()

        self.server.queue.put(("Go", ))

        while not self.shutdown.is_set():
            self.log("Waiting for a message.")
            message = self.queue.get()
            self.handle_message(message)

        self.close_program()

    def close_program(self):

        self.log("Close program.")

    def handle_message(self, message):

        command = message[0]
        args = message[1:]
        if len(args):
            eval("self.{}(*args)".format(command))
        else:
            eval("self.{}()".format(command))

    def server_running(self):
        self.log("Server running.")

    def server_request(self, server_data):
        response = self.game.handle_request(server_data)
        self.server.queue.put(("reply", response))


class BotGame(Logger):

    name = "BotGame"

    def __init__(self, role):
        super().__init__()

        self.role = role

    def handle_request(self, request):

        self.log("Got request: '{}'.".format(request))

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]

        try:
            # retrieve method
            command = eval("self.{}".format(whole[0]))

            # retrieve method arguments
            args = [int(a) if a.isdigit() else a for a in whole[1:]]

            # call method
            to_client = command(*args)

        except Exception as e:
            to_client, to_controller = (
                "Command contained in request not understood.\n"
                "{}".format(e),
                None)

        self.log("Reply '{}' to request '{}'.".format(to_client, request))
        return to_client


def main():

    bot_c = BotController()
    bot_c.run()


if __name__ == "__main__":

    main()