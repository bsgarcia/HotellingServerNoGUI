from datetime import datetime
import inspect
import socket


function_name = lambda: inspect.stack()[1][3]

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.0.0.8', 1027))
    return s.getsockname()[0]

class Logger:

    name = "Logger"

    @classmethod
    def log(cls, msg):

        print("{} {}: {}".format(datetime.now().strftime("[%y/%m/%d %H:%M:%S:%f]"), cls.name, msg))
