package com.example.android.imageclassificationandobjectdetection.liveobjectdetection

import android.content.Context
import android.graphics.RectF
import android.nfc.Tag
import android.util.Log
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import com.example.android.imageclassificationandobjectdetection.AppApplication
import org.tensorflow.lite.support.image.TensorImage
import org.tensorflow.lite.task.vision.detector.ObjectDetector


class SignLanguageDetector(
    private val application: AppApplication, val resultsOverlay:MutableLiveData<List<DetectionResult>>): ImageAnalysis.Analyzer{

    val detector = application.detector



    init {

    }

    @androidx.camera.core.ExperimentalGetImage
    override fun analyze(imageProxy: ImageProxy) {

        Log.d("inside analyze", "${detector}")

        val mediaImage = imageProxy.image ?: return

        val convertImageToBitmap = ImageUtils.convertYuv420888ImageToBitmap(mediaImage)
        val image = TensorImage.fromBitmap(convertImageToBitmap)

        val results = detector?.detect(image)

        val resultToDisplay = results?.map {
            // Get the top-1 category and craft the display text
            val category = it.categories.first()
            val text = "${category.label}, ${category.score.times(100).toInt()}%"

            Log.d("inside analyze", text)

            // Create a data object to display the detection result
            Log.d("inside analyze", "${it.boundingBox.left}")
            DetectionResult(it.boundingBox, text)

        }

        resultToDisplay?.let { resultsOverlay.postValue(resultToDisplay) }

        imageProxy.close()
    }
}

data class DetectionResult(val boundingBox: RectF, val text: String)