import itertools as it
from os import path, mkdir
import json
import pickle
import numpy as np
from datetime import datetime
import copy

from utils.utils import log


class GameManager(object):

    name = "GameManager"

    roles = [(0, 1), (1, 2), (2, 0)]
    n_goods = 3

    file_name = "xp.p"

    def __init__(self):

        self.data = dict()

        # self.give_results = None
        self.continue_game = None
        self.parameters = None
        self.loaded = 0

        self.map_android_id_server_id = dict()
        self.map_android_id_server_id_file = "parameters/map_android_id_server_id.json"

        with open(self.map_android_id_server_id_file) as file:
            self.map_android_id_server_id.update(json.load(file))

        self.n = None
        self.file = None

        self.markets = self.get_markets(self.n_goods)
        self.exchanges_types = self.get_exchange_types(self.n_goods)

        self.command = {
            "get_init": self.get_init,
            "set_choice": self.set_choice
        }

    # -------------------------------------------------------------------------------------- #
    # ----------------------- ON INIT ------------------------------------------------------ #
    # -------------------------------------------------------------------------------------- #

    @staticmethod
    def get_markets(n_goods):

        markets = {}
        for i in it.permutations(range(n_goods), r=2):
            markets[i] = []

        return markets

    @staticmethod
    def get_exchange_types(n_goods):

        return list(it.combinations(range(n_goods), r=2))

    # -------------------------------------------------------------------------------------- #
    # ----------------------- SET-UP ------------------------------------------------------- #
    # -------------------------------------------------------------------------------------- #

    def initialize(self, parameters):

        self.parameters = parameters

        self.continue_game = 1

        if not self.loaded:
            self.prepare_new_session(parameters)

        # self.give_results = np.zeros(self.n)
        self.data["server_id_in_use"] = ["x", ] * self.n

        graphic_data = {
            "statistics": self.get_stats_to_plot(),
            "done_playing": self.data["done_playing"],
            "done_playing_labels": self.data["server_id_in_use"]
        }

        return graphic_data

    # -------------------------------------------------------------------------------------- #
    # ----------------------- ENDING ------------------------------------------------------- #
    # -------------------------------------------------------------------------------------- #

    def last_turn(self):

        self.continue_game = 0
        self.data["end_t"] = self.data["general_t"] + 1

    def end_of_turn(self):

        self.make_encounters()
        self.make_analysis()

        self.data["general_t"] += 1

        if self.data["save"]:
            self.write_on_backup_file()

    def end_of_game(self):

        self.loaded = 0

    # ------------------------------------------------------------------------------------------------------ #
    # --------------------------------------------- FOR PLOT ----------------------------------------------- #
    # ------------------------------------------------------------------------------------------------------ #

    def get_stats_to_plot(self):

        return {
            "exchanges": self.data["exchanges"],
            "consumption": self.data["consumption"],
            "medium_of_exchange": self.data["medium_of_exchange"],
            "n_trial": len(self.data["exchanges"][0])
        }

    # ------------------------------------------------------------------------------------------------------ #
    # --------------------------------------------- PREPARE SESSION ---------------------------------------- #
    # ------------------------------------------------------------------------------------------------------ #

    def create_population(self, parameters):

        structure = np.array([
            parameters["x1"],
            parameters["x2"],
            parameters["x3"]
        ])

        self.n = sum(structure)

        p = np.zeros(self.n, dtype=int)
        c = np.zeros(self.n, dtype=int)
        h = np.zeros(self.n, dtype=int)

        idx = 0

        for i in range(self.n_goods):
            for j in range(structure[i]):
                p[idx] = self.roles[i][0]
                c[idx] = self.roles[i][1]
                h[idx] = self.roles[i][0]

                idx += 1

        return p, c, h

    def load_session(self, file):

        self.loaded = 1

        data = self.load_from_backup_file(file)

        if type(data) == str and data == "error":
            return 0

        else:

            for k, v in data.items():
                self.data[k] = v

            self.n = self.data["n"]

            return {"local": self.data["local"]}

    def prepare_new_session(self, parameters):

        if parameters["save"]:
            self.create_new_backup_file()

        log("Prepare new session.", self.name)

        p, c, h = self.create_population(parameters)

        self.data.update({
            "x1": parameters["x1"],
            "x2": parameters["x2"],
            "x3": parameters["x3"],
            "done_playing": np.zeros(self.n, dtype=int),
            "p": p,
            "c": c,
            "h": h,
            "n": self.n,
            "desired": np.zeros(self.n, dtype=int),
            "success": np.zeros(self.n, dtype=int),
            "reward": np.zeros(self.n, dtype=int),
            "reward_amount": np.zeros(self.n, dtype=int),
            "choice": np.zeros(self.n, dtype=int),
            "medium_of_exchange": [[] for i in range(3)],
            "consumption": [],
            "exchanges": [[] for i in range(3)],
            "server_id_in_use": ["x", ] * self.n,
            "t": np.zeros(self.n, dtype=int),
            "last_reply": np.ones(self.n, dtype=int) * -1,
            "general_t": -1,
            "end_t": -1,
            "map_server_id_game_id": {},
            "random": parameters["random"],
            "save": parameters["save"],
            "local": parameters["local"]
        })

        for i in ["choice", "h", "success"]:
            self.data["hist_{}".format(i)] = []

        log("P: {}".format(p), self.name)
        log("C: {}".format(c), self.name)

    # ------------------------------------------------------------------------------------------------------ #
    # --------------------------------------------- HANDLE REQUEST ----------------------------------------- #
    # ------------------------------------------------------------------------------------------------------ #

    def handle_request(self, request):

        log("Got request: '{}'.".format(request), self.name)

        command = [i for i in request.split("/") if i != ""]
        if command[0] in self.command.keys():
            to_write, message_to_manager, statistics = self.command[command[0]](*command[1:])

        else:
            to_write, message_to_manager, statistics = "Command contained in request not understood.", None, None

        log("Reply '{}' to request '{}'.".format(to_write, request), name=self.name)
        return to_write, message_to_manager, statistics

    def get_init(self, android_id):

        message_to_manager = None

        log("Client with android id {} ask for information.".format(android_id), self.name)

        server_id = self.get_server_id(android_id)
        log("I associate server id '{}' to android id '{}'.".format(server_id, android_id), self.name)
        game_id = self.get_game_id(server_id)
        log("I associate game id '{}' to server id '{}'.".format(game_id, server_id), self.name)

        if game_id != -1:

            relative_h = self.get_relative_good(self.data["h"][game_id], game_id)
            relative_desired = self.get_relative_good(self.data["desired"][game_id], game_id)
            reward_amount = self.data["reward_amount"][game_id]
            done_playing = self.data["done_playing"][game_id]
            # already_had_results = self.give_results[game_id]
            t = self.data["t"][game_id]

            if done_playing:
                state = "ask_result"

            else:
                state = "choice"

            to_write = "reply/init/{}/{}/{}/{}/{}/{}".format(
                server_id,
                relative_h,
                relative_desired,
                reward_amount,
                state,
                t
            )

            message_to_manager = (
                "update_done_playing_labels",
                self.data["server_id_in_use"]
            )

        else:
            to_write = "Error: All game id's have been taken."

        log("Give init information to client {}: '{}'.".format(server_id, to_write), name=self.name)
        return to_write, message_to_manager, None

    def set_choice(self, str_server_id, str_choice, str_t):

        message_to_manager = None
        statistics = None

        server_id = int(str_server_id)
        choice = int(str_choice == "wheat")
        t = int(str_t)

        # Verify that request emanates from a target that already have been registered
        if server_id in self.data["server_id_in_use"]:

            # Retrieve Game ID
            game_id = self.get_game_id(server_id)

            # If choice has not been already set.
            # If 't' given by client is superior to previous t associated with reply,
            # then the choice is not set.

            if t > self.data["last_reply"][game_id]:

                # Set choice
                log("Register choice for client {}.".format(server_id), self.name)
                self.register_choice(game_id, choice, t)

                message_to_manager = (
                    "update_done_playing",
                    self.data["done_playing"]
                )

                # Check for end of trial
                end_of_trial = self.check_for_end_of_trial()
                if end_of_trial:
                    self.end_of_turn()
                    statistics = self.get_stats_to_plot()

            # If signal is given for this client for having results, give him results.
            if t <= self.data["general_t"]:

                self.data["t"][game_id] = t + 1

                log("Give results is set for client {}. I give results".format(server_id), self.name)
                to_write = self.get_results(game_id, t)

            # # Else if game is further away than the client is, give him the previous result
            # elif self.data["general_t"] > t:
            #     log("General t > client t for client {}. I give results".format(server_id), self.name)
            #     to_write = self.get_results(game_id)

            elif t > self.data["general_t"] + 1:
                raise Exception

            elif t > self.data["t"][game_id]:
                raise Exception

            else:
                to_write = "Retry later for having results."

        else:
            to_write = "Tablet not registered."  # self.fatal_error()

        log("Message to client {}: '{}'.".format(server_id, to_write), name=self.name)
        return to_write, message_to_manager, statistics

    def register_choice(self, game_id, choice, t):

        self.data["last_reply"][game_id] = t

        self.data["choice"][game_id] = choice
        self.data["desired"][game_id] = self.get_desired_good(game_id)
        self.data["done_playing"][game_id] = 1

    def get_results(self, game_id, t):

        if t == self.data["end_t"]:
            continue_game = self.continue_game

        else:
            continue_game = 1

        out = "reply/result/{}/{}".format(
            self.data["success"][game_id],  # Success
            continue_game,  # Continue game
        )

        return out

    def check_for_end_of_trial(self):

        return sum(self.data["done_playing"]) == len(self.data["done_playing"])

    def get_relative_good(self, good, game_id):

        if self.data["p"][game_id] == good:
            return "wood"

        elif self.data["c"][game_id] == good:
            return "wheat"

        else:
            return "stone"

    def get_desired_good(self, game_id):

        # Assume exchange is a success
        if self.data["choice"][game_id] == 1:
            return self.data["c"][game_id]

        else:
            if self.data["h"][game_id] == self.data["p"][game_id]:
                return (self.data["p"][game_id] + 2) % self.n_goods

            else:
                return self.data["p"][game_id]

    # --------------------------------------------------------------------------------------------- #
    # ------------------------ ID MANAGER --------------------------------------------------------- #
    # --------------------------------------------------------------------------------------------- #

    def get_server_id(self, android_id):

        server_id, new = self.get_mapping(android_id, self.map_android_id_server_id)
        if new:
            with open(self.map_android_id_server_id_file, "w") as file:
                json.dump(obj=self.map_android_id_server_id, fp=file)

        return server_id

    def get_game_id(self, server_id):

        game_id, new = self.get_mapping(server_id, self.data["map_server_id_game_id"], max_n=self.n)

        if game_id != -1:
            if new:
                self.data["map_server_id_game_id"].update({server_id: game_id})
            self.data["server_id_in_use"][game_id] = server_id

        return game_id

    @staticmethod
    def get_mapping(input_id, mapping, max_n=-1):

        if input_id in mapping.keys():
            output_id = mapping[input_id]
            new = 0

        else:
            if len(mapping) == max_n:
                output_id = -1

            else:
                if len(mapping) > 0:
                    output_id = max(mapping.values()) + 1

                else:
                    output_id = 0

                mapping[input_id] = output_id

            new = 1

        return output_id, new

    def get_server_id_in_use(self):

        return self.data["server_id_in_use"]

    # ----------------------------------------------------------------------------------------------------- #
    # ---------------------------------- BACKUP ----------------------------------------------------------- #
    # ----------------------------------------------------------------------------------------------------- #

    def create_new_backup_file(self):

        with open("parameters/localization.json") as file:
            folder = path.expanduser(json.load(file)["save"])

        if not path.exists(folder):
            mkdir(folder)
        self.file = "{}/xp_{}.p".format(folder, datetime.now().strftime("%y-%m-%d_%H-%M-%S-%f"))

    def write_on_backup_file(self):

        for i in ["choice", "h", "success"]:
            self.data["hist_{}".format(i)].append(copy.deepcopy(self.data[i]))

        with open(self.file, "wb") as file:
            pickle.dump(obj=self.data, file=file)

    def load_from_backup_file(self, file):

        if not path.exists(file):
            return "error"

        else:
            self.file = file
            with open(self.file, "rb") as file:
                try:
                    data = pickle.load(file=file)
                except EOFError:
                    return "error"

            return data

    # ----------------------------------------------------------------------------------------------------- #
    # ---------------------------------- ENCOUNTERS ------------------------------------------------------- #
    # ----------------------------------------------------------------------------------------------------- #

    def make_encounters(self):

        log("Make encounters.", self.name)
        log("Mapping game-server IDs: {}.".format(self.data["map_server_id_game_id"]), self.name)

        self.data["done_playing"][:] = 0

        if self.data["random"]:  # Mode test
            self.random_success()

        else:
            self.manage_markets()

    def random_success(self):

        success = np.random.choice([0, 1], size=self.n)
        for i in range(self.n):
            self.data["success"][i] = success[i]
            if success[i]:
                self.update_in_case_of_success(game_id=0)

        log("Random success: {}".format(self.data["success"]), self.name)

    def manage_markets(self):

        log("Manage markets.", self.name)

        for k in self.markets:
            self.markets[k] = []

        for i in range(self.n):
            # Reinitialize success variable
            self.data["success"][i] = 0

            # Reinitialize reward variable
            self.data["reward"][i] = 0

            agent_choice = (self.data["h"][i], self.data["desired"][i])
            self.markets[agent_choice].append(i)

        success_idx = []

        for i, j in self.exchanges_types:

            a1 = self.markets[(i, j)]
            a2 = self.markets[(j, i)]
            min_a = int(min([len(a1), len(a2)]))

            if min_a:
                selected_from_a1 = list(np.random.choice(a1, size=min_a, replace=False))
                selected_from_a2 = list(np.random.choice(a2, size=min_a, replace=False))

                success_idx += selected_from_a1 + selected_from_a2

                print("Result for market {} and {}:".format((i, j), (j, i)))
                print("Selected for market {}: {}".format((i, j), selected_from_a1))
                print("Selected for market {}: {}".format((j, i), selected_from_a2))

        for i in success_idx:
            self.data["success"][i] = 1
            self.update_in_case_of_success(game_id=i)

        log("Success: {}".format(self.data["success"]), self.name)

    def update_in_case_of_success(self, game_id):

        if self.data["desired"][game_id] == self.data["c"][game_id]:

            self.data["reward_amount"][game_id] += 1
            self.data["reward"][game_id] = 1
            self.data["h"][game_id] = self.data["p"][game_id]

        else:
            self.data["h"][game_id] = self.data["desired"][game_id]

    # ----------------------------------------------------------------------------------------------------- #
    # ---------------------------------- ANALYSIS --------------------------------------------------------- #
    # ----------------------------------------------------------------------------------------------------- #

    def make_analysis(self):

        self.analyse_consumption()
        self.analyse_exchanges()
        self.analyse_medium_of_exchange()

    def analyse_consumption(self):

        log("Rewards: {}.".format(self.data["reward"]), self.name)

        mean_consumption = np.mean(self.data["reward"])
        self.data["consumption"].append(mean_consumption)
        log("Mean consumption: {:.2f}.".format(mean_consumption), self.name)

    def analyse_medium_of_exchange(self):

        for m in range(self.n_goods):

            used = 0
            could_be_used = 0

            for i in range(self.n):

                prod_cons = [
                    self.data["p"][i],
                    self.data["c"][i]
                ]

                if m not in prod_cons:

                    could_be_used += 1

                    if m == self.data["h"][i]:
                        used += 1

            ratio_for_m = used / could_be_used if could_be_used > 0 else 0
            log("Ratio medium of exchange for good {}: {:.2f}.".format(m, ratio_for_m), self.name)
            self.data["medium_of_exchange"][m].append(ratio_for_m)

    def analyse_exchanges(self):

        for idx, (i, j) in enumerate(sorted(self.exchanges_types)):
            a1 = self.markets[(i, j)]
            a2 = self.markets[(j, i)]
            min_a = int(min([len(a1), len(a2)]))

            log("N exchange {}: {}.".format((i, j), min_a), self.name)
            self.data["exchanges"][idx].append(min_a)
