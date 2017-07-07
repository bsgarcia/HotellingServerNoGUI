from bots.bot_client import HotellingPlayer


def main():

    n = 3

    for i in range(n):

        bc = HotellingPlayer(name="HotellingPlayer{}".format(i))
        bc.start()


if __name__ == "__main__":

    main()
