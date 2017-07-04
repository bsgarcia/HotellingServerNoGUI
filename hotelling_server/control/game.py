from utils.utils import log


class Game:

    name = "Game"

    def __init__(self, controller):

        self.controller = controller
        self.command = {"get_init": self.get_init}
    
    def setup(self, parameters):
        
        pass

    def handle_request(self, request):

        log("Got request: '{}'.".format(request), self.name)

        command = [i for i in request.split("/") if i != ""]
        if command[0] in self.command.keys():
            to_client, to_controller = self.command[command[0]](*command[1:])

        else:
            to_client, to_controller = "Command contained in request not understood.", None, None

        log("Reply '{}' to request '{}'.".format(to_client, request), name=self.name)
        return to_client, to_controller

    def get_init(self, *args):

        android_id = args[0]

        game_id = self.controller.id_manager.get_game_id_from_android_id(android_id)
        to_client = "{}".format()
        return game_id, None
