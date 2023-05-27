from warehouse import Warehouse
from person import Person


warehouse = Warehouse()
janet = Person("Janet")
henry = Person("Henry")
janet.visit(warehouse)
henry.visit(warehouse)