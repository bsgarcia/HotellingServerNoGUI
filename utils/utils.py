from datetime import datetime
import inspect


function_name = lambda: inspect.stack()[1][3]


class Logger:

    name = "Logger"

    @classmethod
    def log(cls, msg):

        print("{} {}: {}".format(datetime.now().strftime("[%y/%m/%d %H:%M:%S:%f]"), cls.name, msg))
