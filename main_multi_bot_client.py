from bots.bot_client import HotellingBot


def main():

    n = 1

    for i in range(n):

        # noinspection SpellCheckingInspection
        bc = HotellingBot(name="HotellingBot{}".format(i))
        bc.start()


if __name__ == "__main__":

    main()
