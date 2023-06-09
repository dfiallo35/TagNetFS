import Pyro5.api

class MyServer(object):
    pass

# crea el objeto de servidor
server_obj = MyServer()

# cambia el ID Pyro del objeto
Pyro5.api.current_context.set('PYRO:unique_id@localhost:9999')

# crea y registra el daemon
daemon = Pyro5.api.Daemon()
uri = daemon.register(server_obj)
print(f"URI del servidor: {uri}")

# inicia el requestLoop
print("Iniciando el requestLoop...")
daemon.requestLoop()

# detiene el requestLoop y cierra el daemon
print("Deteniendo y cerrando el daemon...")
daemon.requestLoop.stop()
daemon.close()