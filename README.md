# Tag Based File System

#### Team:
- Dennis Fiallo Muñoz C-411
- Lauren Olivia Guerra Hernández C-412

### How to run

If you don't have the `tagfs.tar` file, you must first create the project image using the docker command `docker build tagfs <project address>`, but if you already have the image you just have to do `docker load -i <image address>`.
Now that you have the image you can change the project settings in the `configs.json` file and how you want to build the nodes in `docker-compose.yml`. Then run the `docker compose up ...` command to activate the nodes.



### Descripción del sistema.

TagFS o Tag based file system es un sistema de ficheros distribuido basado en etiquetas cuyo objetivo es el almacenamiento y consulta de ficheros a través de sus etiquetas asignadas.
El sistema es capaz de mantener la disponibilidad en todo momento, incluso si algunos nodos fallan, y garantiza la integridad de los datos en caso de fallas de almacenamiento. También es capaz de recuperarse y funcionar como un solo sistema, de forma transparente, en caso de que sufra una partición. Es una buena forma de gestionar archivos de forma eficiente y segura.

### Interfaz

La interfaz del sistema es la consola de comandos, se puede llamar al cliente a través de: python client.py y a continuación uno de los siguientes comandos:

- `add -f file -t tag`
  Copia uno o más ficheros hacia el sistema y estos son inscritos con las etiquetas contenidas en tag.
  Ej: `python client.py add -f file1 -f file2 -t tag1 -t tag2 -t tag3`

- `delete -q tag-query`
  Elimina todos los ficheros que cumplan con la consulta tag-query.
  Ej: `python client.py delete -q tag1 -q tag2 -q tag3`

- `list -q tag-query`
  Lista el nombre y las etiquetas de todos los ficheros que cumplan con
  la consulta tag-query.
  Ej: `python client.py list -q tag1 -q tag2`

- `add-tags -q tag-query -t tag`
  Añade las etiquetas contenidas en tag-list a todos los ficheros que cumplan con la consulta tag-query.
  Ej: `python client.py add-tags  -q query1 -q query2 -t tag1`

- `delete-tags -q tag-query -t tag`
  Elimina las etiquetas contenidas en tag-list de todos los ficheros quecumpan con la consulta tag-query.
  Ej: `python client.py delete-tags -f file1 -f file2 -t tag1 -t tag2 -t tag3`

### Arquitectura del sistema:

Se utiliza una arquitectura de sistema distribuido cliente-servidor, donde se tiene:
- Cliente: Parte que se encarga de enviar las solicitudes al sistema y recibir las respuestas.
- Servidor: Parte que se encarga de almacenar los datos y procesar las solicitudes recibidas. Este se divide en:
  - Lider: Este va a hacer función de name-server usando un `NameServerDaemon` proporcionado por Pyro5. En este se van a registrar los nodos pertenecientes a la red. En caso de perder a este nodo, otro nodo de la red ocupa su lugar como lider. Este va a contar con la funcionalidad de:
    - Dispatcher: Se encarga de recibir las solicitudes del cliente y repartirlas entre los workers.
  - Nodo: Este va a registrar en un Daemon sus funcionalidad de:
    - Worker: Parte que se encarga de almacenar los datos y procesar las solicitudes recibidas.

Mientras, los workers trabajan con una base de datos distribuida basada en una arquitectura Master-Slave, donde se dividen en grupos de tamaño $n$ configurable. En cada grupo se tiene un master y $n-1$ slaves, donde el master es el encargado de almacenar el fragmento de la base de datos distribuida y de responder las peticiones o hacer cambios en la base de datos según las peticiones recibidas. Los slaves son nodos encargados de almacenar copias de la base de datos para garantizar la disponibilidad y tolerancia a fallos. De esta manera, si el master falla, uno de los slaves puede asumir su papel y continuar procesando las solicitudes.

<div style="text-align:center;">
  <img width='400' heigth='200' src=imgs/1.jpg alt="Arquitectura del Sistema">
  <br>
  <span style="font-size:16px;">Arquitectura del Sistema</span>
</div>

 

### Comunicación:

La comunicación entre servidores se realiza mediante RPC (Remote Procedure Call), utilizando un proxy para la invocación remota de procedimientos. Mientras que el flujo de la comunicación va de la siguiente manera: el cliente realiza una solicitud al sistema, el dispatcher la recibe, le asigna un id y la envía a uno de los workers para su procesamiento. El worker recibe y procesa esta petición(Los workers si tienen más de una petición que procesar a la vez, las encolan y las van ejecutando por orden de llegada).
Para determinar si la respuesta está lista, el dispatcher le pregunta al worker si ha finalizado la ejecución del procedimiento, utilizando el id del mismo para reconocerlo. Si aún no ha terminado continúa esperando y repite la pregunta después de cierto tiempo. Cuando se tienen los resultados de la petición, el worker los envía al dispatcher, este los recibe y los envía al cliente.


### Consistencia y Replicación:

Para la replicación de los datos, se utiliza una base de datos distribuida que se reparte entre varios nodos, cada uno de los cuales es el master de un grupo. Cada grupo contiene un fragmento de la base de datos, y todos los masters en el grupo tienen una copia completa del fragmento correspondiente. Cada grupo está constituído por un nodo master y varios slaves según la configuración del sistema de cuántos server deben haber por grupo.

Cuando llega una solicitud al sistema, el servidor líder la recibe y la envía a uno de los masters del grupo correspondiente para su procesamiento. El master se encarga de actualizar su copia del fragmento de la base de datos y enviar los cambios a sus slaves, que son nodos encargados de almacenar copias de la base de datos para garantizar la disponibilidad y tolerancia a fallos. De esta manera, si el master falla, uno de los slaves puede asumir su papel y continuar procesando las solicitudes.

La sincronización en nuestro caso ocurre fundamentalmente a nivel de grupo, cada master y cada slave tiene un reloj lógico, donde el objetivo es que estén sincronizados, en caso de un request al master, este luego de cumplirlo aumenta su reloj lógico en 1 y manda a actualizar los relojes de sus slaves, enviando la lista de requests que él acaba de cumplir tal que sean las últimas $k$ instrucciones siendo k la diferencia de sus relojes, si estas instrucciones no se encuentran o no se pueden enviar al slave por alguna otra razón se manda a este a copiar todo el fragmento de base de datos de su master, así se asegura la consistencia en todo momento de cada copia de los datos.

### Tolerancia a fallas:

La implementación realizada partiendo del name-server de python garantiza que en todo momento cualquier nodo del sistema pueda acceder al resto de los nodos, no existiendo posibilidad de desconexión de la red en fragmentos.


Si un nodo se desconecta de la red, falla o se vuelve inaccesible ocurre alguno de los siguientes casos:

- el nodo era el dispatcher del sistema:
El dispatcher tiene una línea de sucesión en la cuál todos los masters del sistema conocen la lista de la línea de succesión hasta ellos, siendo estos el último elemento de su lista. En caso de desconección del dispatcher se pierde el name-server que este tenía

- el nodo era un worker y un master de grupo:

- el nodo era un worker y un slave de un grupo:


