# CV Repository
 In this project an android app is developed which classifies as well as detects english alphabets in American Sign Language.
 
 The project utilizes ML Kit library by Google, which brings Google’s machine learning expertise to mobile developers in a powerful and easy-to-use package.
 
 The app provides the user with three options to help understand the sign language:
 
    1. Image Classification : This option classifies any image captured by the camera using the ImageLabeller package to the 26 letters without highlighting the object detected.
    
    2. Object Detection on Images: This option allows the user to not only classify the alphabet shown but also show the region which was considered in a rectangular box. This uses the tensorflow-lite's  task vision library to implement a tflite model in python using the tensorflow ModelMaker library. The model is obtained by retraining the default model for our use case.
    
    3. Live Object Detection: This option uses the same model as in second option and the cameraX library to show the object Detection in the live preview use case.  
  
