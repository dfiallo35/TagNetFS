| Art   | <a href="#UN">UN</a> | <a href="#E-D">E-D</a> | <a href="#DRA">DRA</a> | <a href="#CNN">CNN</a> | <a href="#ANN">ANN</a> | <a href="#VGGN">VGGN</a> | <a href="#IS">IS</a> | <a href="#ST">ST</a> | <a href="#SWT">SWT</a> |
| :---- | :------------------: | :--------------------: | :--------------------: | :--------------------: | :--------------------: | :----------------------: |  :----------------------: |  :----------------------: | :----------------------: |
| <a href="#chino">chino</a>  |          X           |           X            |           X            |           X            |           X            | X |  |  |  |
| <a href="#olive_satellite">olives</a>  |                      |                       |                       |           X            |                       |  | X|  X|  |
| <a href="#jordipi">jordipi</a>  |                      |                       |                       |           X            |                       |  | X|  | X |












Tags:
* (<a id="UN">UN</a>) U-net
* (<a id="E-D">E-D</a>) Encoder-Decoder network
* (<a id="DRA">DRA</a>) Density Regresion Approach 
* (<a id="CNN">CNN</a>) Convolutional Neural Network
* (<a id="ANN">ANN</a>) AlexNet network
* (<a id="VGGN">VGGN</a>) VGGNet network
* (<a id="BLI">BLI</a>) Bilinear Interpolation
* (<a id="IS">IS</a>) Image Segmentation
* (<a id="ST">ST</a>) Swin Transformer
* (<a id="SWT">SWT</a>) Sliding Window Technique


## Importante
  Es muy probable que hayan contenidos que se usen en muchos artículos y sea inevitable que dos o más personas se terminen estudiando lo mismo, de todas maneras mientras más minimicemos la intercepción más abarcamos y mejor aprovechamos el tiempo

Contents per teammate:
* Leonardo:
   * <a href = "https://www.sciencedirect.com/science/article/pii/S1470160X21002569#b0045" id = "chino">Tree counting with high spatial-resolution satellite imagery based on deep neural networks</a>
      * U-net
      * Encoder-Decoder network
      * Density Regression
      * Bilinear Interpolation
      * Convolutional Neural Network

* Lauren:
  * <a href = "https://ieeexplore.ieee.org/abstract/document/9104983/" id = "image_processing"> An automated method for detection and enumeration of olive trees through remote sensing</a> (Mucho procesamiento de imágenes, nada de ML)
      * Image Segmentation
      * Morphological Operations
      * Blob Detection 
      * Edge Detection      
      * Image Binarization
  * <a href = "https://www.hindawi.com/journals/cin/2022/1549842/" id = "olive_satellite"> A Large-Scale Dataset and Deep Learning Model for Detecting and Counting Olive Trees in Satellite Imagery</a>
      * Region convolutional neural network (R-CNN)
      * Swin Transformer (SwinTUnet) Encoder-Decoder
      * Image Segmentation
  * <a href = "https://openaccess.thecvf.com/content/ICCV2021/papers/Touvron_Going_Deeper_With_Image_Transformers_ICCV_2021_paper.pdf" id = "transform"> Going deeper with Image Transformers</a>
      * Swin Transformer

* Jordan:
  * <a href = "https://www.researchgate.net/profile/Ioannis-Daliakopoulos/publication/273216095_Tree_Crown_Detection_on_Multispectral_VHR_Satellite_Imagery/links/57286d0008aee491cb42f0f6/Tree-Crown-Detection-on-Multispectral-VHR-Satellite-Imagery.pdf" id = "jordipi"> Tree Crown Detection on Multispectral VHR Satellite Imagery</a> (Mucha matemática aplicada, nada de ML)
      * IN Daliakopoulos, EG Grillakis…, 2009
      * Red Band Thresholding
      * Laplacian of the Gaussian (LOG) blob detection method
      * Arbor Crown Enumerator (ACE)
      * Normalized Difference Vegetation Index (NDVI)
      * Calibration
  * <a href = "https://www.mdpi.com/173204" id = "jordipi"> Deep Learning Based Oil Palm Tree Detection and Counting for High-Resolution Remote Sensing Images</a>
      * W Li, H Fu, L Yu, A Cracknell, 2016
      * Convolutional Neural Network (CNN)
      * Deep Learning
      * The Sliding window technique to predict
      * Accuracy more 96%
  * <a href = "https://arxiv.org/abs/1701.06462" id = "jordipi"> Using Convolutional Neural Networks to Count Palm Trees in Satellite Images</a>
      * EK Cheang, TK Cheang, YH Tay, 2017
      * Supervised Learning
      * Convolutional Neural Network (CNN)
      * Uniform Filter
      * Accuracy 94-99%

* Krtucho:
  * <a href = "https://www.mdpi.com/2072-4292/14/3/476" id = "Krtucho"> Transformer for Tree Counting in Aerial Images </a>
      * Convolutional Neural Network (CNN)
      * Density Transformer (DENT)
      * Density Map Generator (DMG)
   * <a href = "https://github.com/A2Amir/Counting-Trees-using-Satellite-Images" id = "Krtucho"> Counting-Trees-using-Satellite-Images </a>
      * Semantic Segmentation
      * U-net
      * Convolutional Neural Network
      * Binary Cross Entropy as the loss function.
      * images (848 × 837 pixels and eight channel) and labeled masks ( has 848 × 837 pixels and five channel): Buildings, Roads and Tracks, Tress, Crops, Water
      * Validation loss of 0.1388, validation accuracy of 0.9447, validation precision of 0.9757 and validation recall of 0.7551.

* Paula:
    *  <a href = "https://www.tandfonline.com/doi/abs/10.1080/01431161.2019.1569282" id = Mubin2019 > Young and mature oil palm tree detection and counting using convolutional neural network deep learning method </a>
        * Mubin et al., 2019
        * Oil palm tree
        * CNN
        * Deep learning
    
    * <a href = "https://www.mdpi.com/1198426" id= "Ammar2021">  Deep-Learning-Based Automated Palm Tree Counting and Geolocation in  Large Farms from Aerial Geotagged Images </a>
        * Ammar et al., 2021
        * CNN
        * Faster R-CNN 
        * You Only Look Once (YOLO)

    * <a href = "https://www.sciencedirect.com/science/article/pii/S030324342100369X" id = "Sun2022"> Cunting trees in a subtropical mega city using the instance segmentation method </a>
        * Sun et al., 2022
        * end to end tree counting deep learning framework in the regional-scale tree detection by delineating each tree crown
        * Cascade mask R-CNN
        * Individual tree detection
