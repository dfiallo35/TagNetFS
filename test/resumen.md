- Mezclar imagenes espectrales con LiDAR mejora sustancialmente los resultados

- snowballing (tecnica para el estado del arte)

- keyword:
  
  - remote sensing
  
  - ~~street view~~
  
  - urban green
  
  - clasification
  
  - terrestrial and laser scanning

- A distinction must be made between the identification of trees that are part of a denser  canopy (e.g., [ 58 ,59 ]) or the identification of single standing trees (e.g., street trees).In an urban forest setting, trees will be located close to each other, so  textural measures derived from the spectral imagery can significantly improve classification,  whereas the utility of this information decreases when dealing with freestanding trees  (e.g., [53 ]). On the other hand, the development of a freestanding tree is often unobstructed  and it can therefore develop properly, making it often more representative for the species  and easier to identify [60]

- The presence of background material in the pixel is often an important source of  confusion when mapping freestanding trees. Unlike in a natural environment, the back-  ground material in an urban setting is often much more diverse, making it difficult to filter  out its influence [ 53 ,54 ]. The spatial resolution of the imagery is of course important in  mitigating these effects: the lower the spatial resolution, the larger the impact of mixing  with background material will be.

- Un problema muy frecuente es que en casos de baja resolución espacial (3,5m) los árboles individuales  no tan densos, con fondos grises (piso) se mezclan y hacen muy ser identificados, esto se arregla con mejorar la resolución espacial

- Categorías
  
  - 1:
    
    - Deciduous:
    
    - Evergreen
  
  - 2:
    
    - Gimnosperma
    
    - Angiosperma

- Co-registration:
  
  - Procedimiento conocido en procesamiento de imágenes
  
  - Cuando se tiene más de una imagen de un mismo lugar, pero desde diferentes sistemas de referencia (inclinadas, rotadas, trasladadas)
  
  - https://www.geodatalab.it/gis-tecnologie/gis-and-co-registration-an-overview/

- Remote sensing Data
  
  - Optical Sensor:
    
    - Se clasifican por : resolucioines espaciales, espectrales y temporales
    
    - Mayor resolución espacial y mayor resolución espectral llevan a mejores resultados pero frecuentemente el incremento de la primera lleva a la disminución de la segunda
    
    - Las sombras de los edificios constituyen una fuente importante de ruido y hay varios enfoques para efrentarlos "Different authors deal with shadow  in different ways, either (a) by omitting elements that are affected by shadow from the  training set (e.g., [ 71 ]), (b) by performing a shadow correction [23 ,46 ] or (c) by including  shadowed areas as a separate class (e.g., [53,58,72])."
    
    - Con resolución de menos de 3m identificar árboles individiuales se vuelve muy difícil
    
    - Los sensores aereos generalmente tienen mejor resolución espacial y espectral
    
    - Los satelites tienden a tirar varias fotos de un mismo lugar por lo que es bueno para el análisis fenológico
  
  - LiDAR:
    
    - Se enfoca principalmente en la altura de los árboles
    
    - Poca resolución (menos de 10 puntos por metro cuadrado)  ya funciona para muchos casos
    
    - Se tiende a fijar en la altura de los árboles para clasificarlos

- Features:
  
  - Spectral Features:
    
    - para imagenes hyperespectrales
    
    - se fija en los valores de una banda específica como el indice de vegetación
    
    - Como el caso de normalized difference vegetation index que se usa para discrimar zonas donde hay vegetación y donde no
    
    - Se puededn usar rangos mas estrechos para tener otras características
  
  - Textural Feutures:
    
    - Información sobre las variaciones espectrales alrededor de un pixel o dentro del area que ocupa el objeto
    
    - Depende mucho de la resolución espacial de las imagenes
    
    - Hay dos tipos  de características de textura:
      
      - primer orden: variacion de reflactancia alrededor del pixel o dentro de la imagen del objeto (copa del árbol)
      
      - segundo orden: información espacial de esta variación (matriz de co-ocurrencia del nivel de gris)
  
  - Geometrical Features:
    
    - Tamaño, forma, ...
    
    - Mientras más variados los tipos que se quieren indentificar más interesnate?
  
  - Contextual Features:
    
    - Buscar información de los objetos que están a su alrededor
    
    - Puede funcionar para clasificar bajo la asumpsion de que árboles del mismo tipo tienden a estar cerca
  
  - LiDAR:
    
    - Informacion de la altura, ancho y forma de la copa del arbol
    
    - La distribucion de puntos dentro de la corona da información de las ramas y las ojas
    
    - Información de la intensidad de retorno
    
    - Se tienden a usar rangos en vez de valores, pq estos tienden a variar

- Image Segmentation:
  
  - Para poder tener un enfoque orientado a objetos:
    
    - Por la alta variabilidad espectral y espacial
    
    - Permite extraer otros features como forma, textura y contexto
  
  - Es muy común usar region growing segmentation
    
    - Tiene problema con el scale-factor que depende mucho del árbol que se quiere segmentar
    
    - Por lo anterior se usa un enfoque herarquico con varios niveles de segmentación
  
  - El LiDAR puede ayudar:
    
    - Un filtro de máximo local en un canopy height model (CHM) combinado con el filtro NDVI, tiene muchos problemas

- Clasification Approach:
  
  - Usar decision trees
    
    - Mientras más grandes son los grupos en los que se clasifican más fácil es clasificar
    
    - En muchos casos es suficiente con el NDVI y la altura para discriminar entre varias clases

- Supervised Learning Approach:
  
  - El más popular
  
  - Se pueden clasificar en paramétricos o no paramétricos
    
    - Paramétricos:
      
      - Asume cosas sobre la distribución de los datos
      
      - Son de interés porque son fáciles de interpretar
      
      - Rápidos
      
      - Requieren de menos entrenamiento
    
    - No Paramétricos:
      
      - No asume cosas de la distribución de los datos
      
      - Puede tener mejores resultados por no asumir nada de la distribución de los datos
      
      - Son más comunes de usar
  
  - Métodos paramétricos más utilizados:
    
    - Maximum Likelihood classifier 
    
    - Discriminant análisis
      
      - Linear Discriminant Análsis
      
      - Canónical Discriminant Análisis
      
      - Stepwise Discriminant Análisis
        
        - Da peores resultados que los otros dos
  
  - Métodos No Paramétricos más utilizados
    
    - SVM
    
    - Arboles de decisión
    
    - Deep Learning está ganando popularidad
      
      - Se usa más con imagenes de Street View y para contar a nivel de especie
  
  - SVM
    
    - Produjo mejores resultados que un ML clasifier para pixel-based clasification para clasficar entre 3 especies
    
    - Con información multi-temporal SVM se desempeñó mucho mejor que CART (árboles de decisión). El autor cree que fué porque SVM lidió mejor con los datos desbalanceados y de alta dimensión de su training set
  
  - ML clasifier
    
    - Lo compararon con árboles de decisión para distinguir si un árbol es oak o no y dieron majomeno igual
    
    - Lo compararon con árboles de decisión para clasificar entre árboles con ojas anchas, con hojas de aguja, cesped artificial o hierba normal usando object-based clasification y los árboles de decisión dieron 75 y el enfoque con ML 88
  
  - Decisión Tree
    
    - Lo compararon con LDA para clasificar 7 especies y resultó peor, pero ambos dieron malos resultados (65)
  
  - Linear discriminant
    
    - Mejor que Decisión tree para muchas especies pero igual da malos resultados
  
  - Ensemble
    
    - El más popular es random forest
    
    - Fue un poco mejor usando imagenes bi-temporales para clasificar entre dos especies
    
    - Cuando se tiene pocos ejemplos de entrenamiento y datos muy ruidosos hacer una combinación de muchos clasificadores  da buenos resultados
  
  - Se hizo un estudio donde se comparó KNN, decisión tree, multi-layer perceptrón y random forest y los mejores resultados fueron para los dos últimos. Usaron más de 100 ejemplo por cada especie que querían clasificar, y los bordes de los árboles fueron delineados manualmente

- Library-Based Clasification
  
  - Talla super turbea de análisis hyperespectral
  
  - Spectral Mixture Análisis
  
  - Spectral Angle Mapper
  
  - [Spatial/Spectral Browsing and Endmembers - L3Harris Geospatial](https://www.l3harrisgeospatial.com/Learn/Blogs/Blog-Details/ArtMID/10198/ArticleID/15766/SpatialSpectral-Browsing-and-Endmembers)
  
  - Al fijarse en tanto nivel de detalle cuando hay muchas especies en juego se vuelve muy difícil abarcarlas a todas

- Deep Learning
  
  - Algoritmos que ellos creen que destacaron:
    
    - Boltzman machine
      
      - Mejores features que métodos tradicionales de reducción de dimensión como (PCA)
    
    - Multiple Layer Perceptron
      
      - Buen accuracy con 4 hidden layers con high-resolution RGB images para distinguir entre vegetación alta y baja
    
    - CNN:
      
      - 93 de accuracy para distinguir entre evregreen, decidious y llerva usando información multi-temporal
      
      - Dense net con 83 de accuracy en clasificar 8 tipos de árboles que SVM y RF hacen 52

Decisions:

- Tipo de vegetación

- Seleccion del tipo de remote sensing data a utilizar

- Selección del método

Active Learning casi no se ha usado a pesar de que es reconocido por funcionar bien con  remote sensing data

Unsupervised Learning puede encontrar nuevas formas de clasificar los datos en vez de las conocidas clases de árboles
