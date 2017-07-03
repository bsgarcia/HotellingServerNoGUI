from os import path, mkdir
import json
import pickle
from datetime import datetime


class Backup:

    def __init__(self, controller):

        self.controller = controller
        self.file = "{}/xp_{}.p".format(self.folder, datetime.now().strftime("%y-%m-%d_%H-%M-%S-%f"))
        self.data = None

    @property
    def folder(self):

        with open("parameters/localization.json") as file:
            folder = path.expanduser(json.load(file)["save"])

        if not path.exists(folder):
            mkdir(folder)
        return folder

    def write(self):

        with open(self.file, "wb") as file:
            pickle.dump(obj=self.data, file=file)

    def load(self, file):

        if not path.exists(file):
            return "error"

        else:
            self.file = file
            with open(self.file, "rb") as file:
                try:
                    self.data = pickle.load(file=file)
                except EOFError:
                    return "error"

            return self.data

