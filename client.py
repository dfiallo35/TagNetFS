from app.client.client import Client


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()

    HOST = args.host
    PORT = args.port

    client = Client(HOST, PORT)
    client.connect()