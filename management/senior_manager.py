from threading import Thread
from multiprocessing import Event, Queue

from utils.utils import log
from management.game_manager import GameManager
from server.server import ServerManager


class SeniorManager(Thread):

    name = "SeniorManager"

    def __init__(self, manager_queue, graphic_queue, communicate):

        super().__init__()
        
        # For receiving inputs
        self.manager_queue = manager_queue
        
        # For giving instructions to graphic process
        self.graphic_queue = graphic_queue
        self.communicate = communicate
        
        # For giving go signal to server
        self.server_queue = Queue()
        self.running_game = Event()
        
        self.server_manager = ServerManager(
            server_queue=self.server_queue,
            manager_queue=self.manager_queue,
            running_game=self.running_game
        )
        self.game_manager = GameManager()
        
        self.shutdown = Event()
        self.fatal_error = Event()
        self.continue_game = Event()

    def run(self):

        log("Waiting for a message.", name=self.name)
        message = self.manager_queue.get()
        log("Got message: {}".format(message), name=self.name)

        self.ask_interface("show_load_game_new_game")
        
        # Launch server manager
        self.server_manager.start()

        while not self.shutdown.is_set():
            log("Waiting for a message.", name=self.name)
            message = self.manager_queue.get()
            self.handle_message(message)

        self.close_program()

    def launch_game(self, parameters):

        self.ask_interface("show_setting_up_frame")

        # Stop server if he was previously running
        self.server_manager.shutdown()

        # Go signal for launching the (properly speaking) server
        self.server_queue.put(("Go", parameters["local"]))

        self.fatal_error.clear()
        self.continue_game.set()
        self.running_game.set()

        graphic_data = self.game_manager.initialize(parameters)

        self.ask_interface("show_experimental_frame", graphic_data)

        log("Game launched.", self.name)

    def stop_game_first_phase(self):

        log("Received stop task", self.name)
        self.continue_game.clear()
        self.game_manager.last_turn()
        # Wait then for a signal of the request manager for allowing interface to show a button to starting menu

    def stop_game_second_phase(self):

        self.game_manager.end_of_game()
        self.running_game.clear()
        self.ask_interface("show_load_game_new_game")

    def close_program(self):

        log("Close program.", self.name)
        self.shutdown.set()
        self.running_game.set()
        
        # For aborting launching of the (properly speaking) server if it was not launched
        self.server_queue.put(("Abort", ))
        
        # Stop server if it was running
        self.server_manager.end()
        self.server_manager.shutdown()
        log("Program closed.", self.name)

    def fatal_error_of_communication(self):

        if not self.fatal_error.is_set():
            self.fatal_error.set()
            self.running_game.clear()
            self.continue_game.clear()

            self.ask_interface("fatal_error_of_communication")
        
    def ask_interface(self, instruction, arg=None):

        self.graphic_queue.put((instruction, arg))
        self.communicate.signal.emit()


# ------------------------------- MESSAGE HANDLING ----------------------------------------------- #

    def handle_message(self, message):

        log("Received message '{}'.".format(message), name=self.name)

        if message[0] == "server":
            self.handle_server(message[1:])

        elif message[0] == "interface":
            self.handle_interface(message[1:])

        elif message[0] == "parameters_frame":
            self.handle_parameters_frame(message[1:])

        elif message[0] == "experimental_frame":
            self.handle_experimental_frame(message[1:])

        elif message[0] == "load_game_new_game":
            self.handle_load_game_new_game(message[1:])

        else:
            raise Exception("{}: Received message '{}' but did'nt expected anything like that."
                            .format(self.name, message))

    def handle_interface(self, message):

        information = message[0]

        if information == "close":
            self.close_program()

        elif information == "retry":
            self.server_queue.put(("Go", ))

        else:
            raise Exception(
                "{}: Received message '{}' emanating from 'interface' "
                "but did'nt expected anything like that.".format(self.name, message)
            )

    def handle_server(self, message):

        information = message[0]

        if information == "error":
            log("Error server", name=self.name)
            self.ask_interface("server_error")

        elif information == "running":

            log("Server running.", name=self.name)

        elif information == "request":

            request = message[1]
            response, message, statistics = self.game_manager.handle_request(request)
            self.server_queue.put(("reply", response))
            if message is not None:
                information = message[0]

                if information == "update_done_playing":
                    done_playing = message[1]
                    self.ask_interface("update_done_playing", done_playing)

                elif information == "update_done_playing_labels":
                    done_playing_labels = message[1]
                    self.ask_interface("update_done_playing_labels", done_playing_labels)

                elif information == "fatal_error":
                    self.fatal_error_of_communication()

            if statistics is not None:

                self.ask_interface("update_statistics", statistics)

                # If was waiting for ending game
                if not self.continue_game.is_set():
                    self.ask_interface("update_stop_button_experimental_frame")

        else:
            raise Exception(
                "{}: Received message '{}' emanating from 'server' "
                "but did'nt expected anything like that.".format(self.name, message)
            )

    def handle_load_game_new_game(self, message):

        information = message[0]

        if information == "new":
            self.ask_interface("show_parameters_frame")

        elif information == "load":
            self.ask_interface("file_dialog")

        elif information == "file":
            file = message[1]

            parameters = self.game_manager.load_session(file)
            if parameters:
                self.launch_game(parameters)

            else:
                self.ask_interface("error_load_session")

        else:
            raise Exception("{}: Received message '{}' emanating from 'load_game_new_game' "
                            "but did'nt expected anything like that."
                            .format(self.name, message))

    def handle_experimental_frame(self, message):

        information = message[0]

        if information == "stop":
            if self.continue_game.is_set():
                self.stop_game_first_phase()
            else:
                self.stop_game_second_phase()

        else:
            raise Exception("{}: Received message '{}' emanating from 'experimental_frame'"
                            "but did'nt expected anything like that."
                            .format(self.name, message))

    def handle_parameters_frame(self, message):

        information = message[0]
        if information == "parameters":
            parameters = message[1]
            log("Received parameters.", name=self.name)
            self.launch_game(parameters)
