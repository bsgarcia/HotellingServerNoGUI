from utils.utils import log


class Game:

    name = "Game"

    def __init__(self, controller):

        self.controller = controller
        self.command = {}
    
    def setup(self, parameters):
        
        pass

    def handle_request(self, request):

        log("Got request: '{}'.".format(request), self.name)

        command = [i for i in request.split("/") if i != ""]
        if command[0] in self.command.keys():
            to_write, message_to_controller, statistics = self.command[command[0]](*command[1:])

        else:
            to_write, message_to_controller, statistics = "Command contained in request not understood.", None, None

        log("Reply '{}' to request '{}'.".format(to_write, request), name=self.name)
        return to_write, message_to_controller, statistics
