from os import path, mkdir, getcwd
import json
import pickle
from datetime import datetime
from utils.utils import Logger


class Backup(Logger):

    def __init__(self, controller):

        self.controller = controller
        self.file = "{}/xp_{}.p".format(self.folder, datetime.now().strftime("%y-%m-%d_%H-%M-%S-%f"))

    @property
    def folder(self):
        folder = getcwd() + "/results"

        if not path.exists(folder):
            mkdir(folder)
        return folder

    def write(self, data):

        self.log("Saving data to {}".format(self.file))

        with open(self.file, "wb") as file:
            pickle.dump(obj=data, file=file)

    def load(self, file):

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

    @staticmethod
    def save_param(key, new_value):

        # noinspection SpellCheckingInspection
        with open("hotelling_server/parameters/{}.json".format(key), "w") as param_file:
            json.dump(new_value, param_file)
