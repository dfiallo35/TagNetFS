import Pyro5.api
import Pyro5.core
import Pyro5.server
import Pyro5.client
import Pyro5.nameserver
from threading import Thread
import socket


import Pyro5.api
from Pyro5.api import Proxy
from Pyro5.nameserver import NameServer


ns: NameServer|Proxy = Pyro5.api.locate_ns()

print(ns)
print()
print(ns.list())
print()


uri = ns.lookup("a")

a = Pyro5.api.Proxy(uri)
print(a.get_fortune('Hi'))

# Pyro5.api.Proxy("PYRONAME:objectname")
# uri = Pyro5.core.resolve("PYRONAME:objectname")
# # uri now is the resolved 'objectname'
# obj = Pyro5.client.Proxy(uri)

# a = input('>>>')
# print(obj.get_fortune(a))