from bots.bot_client import HotellingBot


def main():

    n = 4

    for i in range(n):

        bc = HotellingBot(name="HotellingBot{}".format(i))
        bc.start()


if __name__ == "__main__":

    main()
