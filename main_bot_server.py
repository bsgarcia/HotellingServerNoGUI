from bots.bot_server import main
import sys

if __name__ == "__main__":

    if len(sys.argv) > 0:
        type_of_player = sys.argv[1]
    else:
        raise Exception("You should indicate a type of player such as 'customer' or 'firm'.")

    main(type_of_player)
