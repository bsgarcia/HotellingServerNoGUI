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
        self.device_scanning_event = Event()

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

        self.close_program()

    def launch_game(self):

        self.ask_interface("show_frame_setting_up")

        self.fatal_error.clear()
        self.continue_game.set()
        self.running_game.set()

        self.start_server()

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

        # For aborting launching of the (properly speaking) 
        # server if it was not launched
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

        if arg is not None:
            self.graphic_queue.put((instruction, arg))
        else:
            self.graphic_queue.put((instruction, ))
        self.communicate.signal.emit()

    def stop_server(self):

        self.log("Stop server.")
        self.server.shutdown()
        self.server.wait_event.set()

    def start_server(self):

        if not self.running_server.is_set():
            self.server.start()

        self.server_queue.put(("Go", ))

    def scan_network_for_new_devices(self):

        self.start_server()
        self.device_scanning_event.set()

    def add_device_to_map_android_id_server_id(self, server_data):

        android_id = server_data.split("/")[-1]
        self.id_manager.get_ids_from_android_id(android_id, max_n=1)

        response = "error/adding_new_device"
        self.server_queue.put(("reply", response))
        self.stop_server()

        self.device_scanning_event.clear()
        self.ask_interface("stop_scanning_network")
     
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

    # ------------------------------ Server interface ----------------------------------------#

    def server_running(self):

        self.log("Server running.")
        self.running_server.set()
        self.server.wait_event.clear()

    def server_error(self, error_message):

        self.log("Server error.")
        self.ask_interface("server_error", error_message)

    def server_request(self, server_data):
        
        # when using device manager to add new clients to json mapping
        if self.device_scanning_event.is_set():

            self.add_device_to_map_android_id_server_id(server_data)
        
        # When game is launched
        else:

            response = self.game.handle_request(server_data)
            self.server_queue.put(("reply", response))
   
    # ------------------------------ UI interface  -------------------------------------------#

    def ui_run_game(self, interface_parameters):
        self.log("UI ask 'run game'.")
        self.data.new()
        self.time_manager.setup()
        self.launch_game()
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

    def ui_save_game_parameters(self, key, value):
        self.log("UI ask 'save game parameters'.")
        self.data.save_param(key, value)
        self.log("Save interface parameters.")

    def ui_stop_bots(self):
        self.log("UI ask 'stop bots'.")
        self.game.stop_bots()

    def ui_stop_server(self):
        self.log("UI asks 'stop server'.")
        self.stop_server()

    def ui_look_for_alive_players(self):

        if self.game.is_ended():

            self.ask_interface("show_frame_load_game_new_game")
            self.stop_server()
            self.game.stop_bots()

        else:

            self.ask_interface("force_to_quit_game")

    # ------------------------------ Time Manager interface ------------------------------------ #

    def time_manager_stop_game(self):
        self.log("'TimeManager' asks 'stop game'.")
        self.stop_game_second_phase()

    def time_manager_compute_figures(self):

        self.log("'TimeManager' asks 'compute_figures'")

        # Needs to be moved elsewhere?
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
