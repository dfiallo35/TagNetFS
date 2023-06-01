# Roles:
- Almacenar datos
- Enrutar pedidos
- Consultar el sistema



# Transparencia:
- Acceso: Oculta diferencias de repr de datos y como se accede
- Ubicacion: oculta donde se ubican
- Migracion: oculata que puedan migrar
- reubicacion: Puede moverse cuando se esta usando
- replica: pueden existir varias replicas, no se distinguen de la que se esta usando
- Concurrencia: un recurso puede usarse por mas de un usuario
- fallas: oculta fallas y recuperacion de recursos
- persistencia: ...

- Configurable: tipos de cifrado, numero de replicas, ...

# Escalabiliad:
- tamanno: permitir crecimiento en procesos, nodos o usuarios sin afectaciones
- distancia: permitir reubicar componentesde los sistemas en lugares fisicamente distantes.
- administracion: deben ser configurables, incluso si abarcan organizaciones diferentes.


# tecnicas:
- distribucuion: dividir procesamiento entre diferentes pc
- replicacion: hacer copias de los datos en diferentes lugares
- caching: proporcionanr copias de los datos a lso clientes.



# Todo:
- Replicacion: 9
- Coordinacion: 5
- Sincronizacion: 7
- tolerancia a fallas: 10
- nombrado: 6
- caching





# Nombrado:

- Conveniente alta disponibilidad del nivel global.
- Conveniente el empleo de caching y replicación.
- Conveniente alta disponibilidad del nivel administrativo dentro de la organización.





# Implementacion:
- Arquitectura cliente-servidor?
- protocolo TCP/IP o RPC?
- Servidores concurrentes
- Punto de entrada desconocido o fijo?
- Servidor guarda informacion por clientes o en general?
- Crear docker-compose