from datetime import datetime


def log(msg, name):

    print("{} {}: {}".format(datetime.now().strftime("[%y/%m/%d %H:%M:%S:%f]"), name, msg))
