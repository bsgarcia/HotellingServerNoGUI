from datetime import datetime


class Logger:

    name = "Logger"

    @classmethod
    def log(cls, msg):

        print("{} {}: {}".format(datetime.now().strftime("[%y/%m/%d %H:%M:%S:%f]"), cls.name, msg))
