from fake_client.fake_client import FakeClient


if __name__ == "__main__":

    n = 40

    for i in range(n):
        fc = FakeClient()
        fc.start()
