import Pyro5
import Pyro5.api
import Pyro5.nameserver as ns
from Pyro5.nameserver import NameServer
import socket
import typer
import threading

app = typer.Typer()


@app.command()
def n():
    t = threading.Thread(target=lambda h, p: ns.start_ns_loop(h, p), args=(socket.gethostbyname(socket.gethostname()), 9090), daemon=True)
    t.start()
    
    # n = ns.start_ns_loop(socket.gethostbyname(socket.gethostname()), 9090)

    print()
    nss:Pyro5.api.Proxy = Pyro5.api.locate_ns()
    print(nss._pyroUri.host)

    # n = Pyro5.api.Proxy(n[0])
    
    # import Pyro5.core


    # print()
    # print(nss == n)
    # print(nss)
    # print(n)
    # print()

    while True: ...
    # ns.start_ns_loop(socket.gethostbyname(socket.gethostname()), 9090)



@app.command()
def a(
    name: str = typer.Option(..., '-n', '--name')
):
    nss=Pyro5.api.locate_ns()
    nss: NameServer
    
    nss.register(name, f'PYRO:{name}@10.0.0.4:9090')
    print()
    print(nss.lookup(name), end='\n')



if __name__ == '__main__':
    app()
