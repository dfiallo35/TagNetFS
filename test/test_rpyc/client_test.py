import rpyc



class Client:
    def run(self):
        conn = rpyc.connect('10.0.0.2', 9090)
        conn.root.append(2)
        conn.root.append(4)
        print(conn.root.value())


c = Client()
c.run()