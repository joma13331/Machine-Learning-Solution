package com.example.android.imageclassificationandobjectdetection

import android.app.Application
import org.tensorflow.lite.task.vision.detector.ObjectDetector

class AppApplication: Application() {

    val options = ObjectDetector.ObjectDetectorOptions.builder()
        .setMaxResults(1)
        .setScoreThreshold(0.0f)
        .build()

    var detector: ObjectDetector? = null
}