from multiprocessing import Queue, Event
from threading import Thread

from utils.utils import Logger
from hotelling_server.control import backup, data, game, server, statistician, id_manager, time_manager


class Controller(Thread, Logger):

    name = "Controller"

    def __init__(self, model):

        super().__init__()

        self.mod = model

        # For receiving inputs
        self.queue = Queue()

        self.running_game = Event()
        self.running_server = Event()

        self.shutdown = Event()
        self.fatal_error = Event()
        self.continue_game = Event()

        self.data = data.Data(controller=self)
        self.time_manager = time_manager.TimeManager(controller=self)
        self.id_manager = id_manager.IDManager(controller=self)
        self.backup = backup.Backup(controller=self)
        self.statistician = statistician.Statistician(controller=self)
        self.server = server.Server(controller=self)
        self.game = game.Game(controller=self)

        # For giving instructions to graphic process
        self.graphic_queue = self.mod.ui.queue
        self.communicate = self.mod.ui.communicate
       
        # Last command received
        self.last_request = None

        # For giving go signal to server
        self.server_queue = self.server.queue

    def run(self):

        self.log("Waiting for a message.")
        go_signal_from_ui = self.queue.get()
        self.log("Got go signal from UI: '{}'.".format(go_signal_from_ui))

        self.ask_interface("show_frame_setting_up")
        self.ask_interface("show_frame_load_game_new_game")

        while not self.shutdown.is_set():

            self.log("Waiting for a message.")
            message = self.queue.get()
            self.handle_message(message)
            self.last_request = message[0]

        self.close_program()

    def launch_game(self):

        self.ask_interface("show_frame_setting_up")

        self.fatal_error.clear()
        self.continue_game.set()
        self.running_game.set()

        # Launch server manager
        if not self.running_server.is_set():
            self.server.start()

        self.server_queue.put(("Go", ))

        self.ask_interface("show_frame_game", self.get_current_data())

        self.log("Game launched.")

    def stop_game_first_phase(self):

        self.log("Received stop task")
        self.continue_game.clear()
        self.time_manager.stop_as_soon_as_possible()

    def stop_game_second_phase(self):

        self.running_game.clear()

    def close_program(self):

        self.log("Close program.")
        self.running_game.set()

        # For aborting launching of the (properly speaking) server if it was not launched
        self.server_queue.put(("Abort",))
        self.server.shutdown()
        self.server.end()
        self.shutdown.set()

    def fatal_error_of_communication(self):

        if not self.fatal_error.is_set():
            self.fatal_error.set()
            self.running_game.clear()
            self.continue_game.clear()

            self.ask_interface("fatal_error_of_communication")

    def ask_interface(self, instruction, arg=None):

        self.graphic_queue.put((instruction, arg))
        self.communicate.signal.emit()

    def stop_server(self):
        self.server.wait_event.set()
        self.server.shutdown()
        self.log("Stop server.")

    # ------------------------------- Message handling ----------------------------------------------- #

    def handle_message(self, message):

        try:
            command = message[0]
            args = message[1:]
            if len(args):
                eval("self.{}(*args)".format(command))
            else:
                eval("self.{}()".format(command))

        except Exception as err:
            self.ask_interface("fatal_error", str(err))

    # ------------------------------ Server interface -----------------------#
    def server_running(self):
        self.log("Server running.")
        self.running_server.set()

    def server_error(self, error_message):
        self.log("Server error.")
        self.ask_interface("server_error", error_message)

    def server_request(self, server_data):
        response = self.game.handle_request(server_data)
        self.server_queue.put(("reply", response))

    # ------------------------------ UI interface (!!!) ----------------------#

    def ui_run_game(self, interface_parameters):
        self.log("UI ask 'run game'.")
        self.launch_game()
        self.time_manager.setup()
        self.game.new(interface_parameters)

    def ui_load_game(self, file):
        self.log("UI ask 'load game'.")
        self.data.load(file)
        self.time_manager.setup()
        self.launch_game()
        self.game.load()

    def ui_stop_game(self):
        self.log("UI ask 'stop game'.")
        self.stop_game_first_phase()

    def ui_close_window(self):
        self.log("UI ask 'close window'.")
        self.close_program()

    def ui_retry_server(self):
        self.log("UI ask 'retry server'.")
        self.server_queue.put(("Go",))

    def ui_save_game_parameters(self, key, data):
        self.log("UI ask 'save game parameters'.")
        self.data.save_param(key, data)
        self.log("Save interface parameters.")

    def ui_stop_bots(self):
        self.log("UI ask 'stop bots'.")
        self.game.stop_bots()

    def ui_look_for_alive_players(self):

        if self.game.game_ended():
            self.stop_server()
            self.game.stop_bots()
            self.ask_interface("show_frame_load_game_new_game")

        else:
            self.ask_interface("force_to_quit_game")

    # ------------------------------ Game interface (!!!) -------------------------------------- #

    def game_stop_game(self):
        self.log("'Game' asks 'stop game'.")
        self.stop_game_second_phase()

    # def update_tables_interface(self):
        # self.log("'Game' asks 'update_tables_interface")
        # self.ask_interface("update_tables")

    def compute_figures(self):
        self.log("'Game' asks 'compute_figures'")

        # needs to be moved elsewhere?
        self.statistician.compute_distance()
        self.statistician.compute_mean_extra_view_choices()
        self.statistician.compute_profits()
        self.statistician.compute_mean_utility()

    # ---------------------- Parameters management -------------------------------------------- #

    def get_current_data(self):

        return {
                "current_state": self.data.current_state,
                "bot_firms_id": self.data.bot_firms_id,
                "firms_id": self.data.firms_id,
                "bot_customers_id": self.data.bot_customers_id,
                "customers_id": self.data.customers_id,
                "roles": self.data.roles,
                "time_manager_t": self.data.controller.time_manager.t,
                "statistics": self.statistician.data,
                "map_server_id_game_id": self.data.map_server_id_game_id
               }

    def get_parameters(self, key):

        return self.data.param[key]

