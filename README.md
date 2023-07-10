# Tag Based File System

#### How to run

To run the code, you must first install the python dependencies found in requirements.txt with `pip install -r requirements.txt`.

### Requisitos del sistema:



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

Se utiliza una arquitectura de sistema distribuido cliente-servidor, se tiene un servidor que actúa como líder y tiene la funcionalidad de dispatcher, es decir, recibe las request del cliente y las reparte entre los diferentes nodos que actúan como workers, estos son los nodos encargados de almacenar fragmentos de la base de datos distribuida y de responder las peticiones o hacer cambios e la base de datos según las peticiones recibidas.
 

### Comunicación:

La comunicación entre servidores se realiza mediante RPC (Remote Procedure Call), utilizando las funciones que son visibles gracias a Pyro Expose.

Cuando el cliente realiza una solicitud al sistema, el dispatcher la recibe, le asigna un id y la envía a uno de los workers para su procesamiento. El worker recibe y procesa esta petición. Los workers si tienen más de una petición que procesar a la vez, las encolan y las van ejecutando por orden de llegada.

Para determinar si la respuesta está lista, el dispatcher le pregunta al worker si ha finalizado la ejecución del procedimiento, utilizando el id del mismo para reconocerlo. Si la respuesta es negativa continúa esperando y repite la pregunta después de cierto tiempo. Si la respuesta es afirmativa, el servidor invoca al cliente a través del proxy y le proporciona los resultados.



### Nombrado y Localización:


### Sincronización:


### Consistencia y Replicación:

Para la replicación de los datos, se utiliza una base de datos distribuida que se reparte entre varios nodos, cada uno de los cuales es el master de un grupo. Cada grupo contiene un fragmento de la base de datos, y todos los masters en el grupo tienen una copia completa del fragmento correspondiente.

Cuando llega una solicitud al sistema, el servidor líder la recibe y la envía a uno de los masters del grupo correspondiente para su procesamiento. El master se encarga de actualizar su copia del fragmento de la base de datos y enviar los cambios a sus slaves, que son nodos encargados de almacenar copias de la base de datos para garantizar la disponibilidad y tolerancia a fallos. De esta manera, si el master falla, uno de los slaves puede asumir su papel y continuar procesando las solicitudes.


### Tolerancia a fallas:
