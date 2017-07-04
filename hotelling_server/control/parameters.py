import json


class Parameters:

    def __init__(self, controller):

        self.controller = controller
        self.keys = ["network", "game", "folders", "map_android_id_server_id", "interface"]
        self.param = {}
        self.setup()

    def setup(self):

        for key in self.keys:
            with open("hotelling_server/parameters/{}.json".format(key)) as file:
                self.param[key] = json.load(file)

    def save(self, key, new_value):

        with open("hotelling_server/parameters/{}.json".format(key), "w") as param_file:
            json.dump(new_value, param_file)

        self.param[key] = new_value

