package com.example.android.imageclassificationandobjectdetection.liveobjectdetection

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.*
import android.os.Bundle
import android.util.Log
import android.view.*
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.MutableLiveData
import com.example.android.imageclassificationandobjectdetection.AppApplication
import com.example.android.imageclassificationandobjectdetection.R
import com.example.android.imageclassificationandobjectdetection.databinding.FragmentLiveObjectDetectionBinding
import org.tensorflow.lite.task.vision.detector.ObjectDetector
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors


class LiveObjectDetectionFragment : Fragment() {

    private lateinit var cameraExecutor: ExecutorService
    private lateinit var binding: FragmentLiveObjectDetectionBinding
    private var drawOk = true
    private var displayId: Int = -1
    var resultOverlay = MutableLiveData<List<DetectionResult>>()
    private lateinit var viewFinder: PreviewView
    private var camera: Camera? = null
    private lateinit var overlay: SurfaceView

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {

        binding = FragmentLiveObjectDetectionBinding.inflate(inflater, container, false)
        // Inflate the layout for this fragment
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        viewFinder = binding.viewFinder
        overlay = binding.overlay
        overlay.apply {
            setZOrderOnTop(true)
            holder.setFormat(PixelFormat.TRANSPARENT)
            holder.addCallback(object : SurfaceHolder.Callback {
                override fun surfaceCreated(p0: SurfaceHolder) {
                    drawOk = true
                }

                override fun surfaceChanged(p0: SurfaceHolder, p1: Int, p2: Int, p3: Int) {
                    drawOk = true
                }

                override fun surfaceDestroyed(p0: SurfaceHolder) {
                    drawOk = false
                }
            })
        }
        cameraExecutor = Executors.newSingleThreadExecutor()


        resultOverlay.observe(
            viewLifecycleOwner,
            { drawOverlay(resultOverlay.value, overlay.holder) })
        if (allPermissionsGranted()) {
            viewFinder.post {
                // Keep track of the display in which this view is attached
                displayId = viewFinder.display.displayId

                // Set up the camera and its use cases
                startCamera()
            }
        } else {
            ActivityCompat.requestPermissions(
                requireActivity(), REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS
            )
        }
    }

    private fun drawOverlay(results: List<DetectionResult>?, holder: SurfaceHolder) {

        val canvas: Canvas? = holder.lockCanvas()

        canvas?.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR)
        val pen = Paint()
        pen.textAlign = Paint.Align.LEFT

        if (drawOk) {
            results?.forEach {
                // draw bounding box
                pen.color = Color.RED
                pen.strokeWidth = 8F
                pen.style = Paint.Style.STROKE
                val box = it.boundingBox
                canvas?.drawRect(box, pen)


                val tagSize = Rect(0, 0, 0, 0)

                // calculate the right font size
                pen.style = Paint.Style.FILL_AND_STROKE
                pen.color = Color.YELLOW
                pen.strokeWidth = 2F

                pen.textSize = MAX_FONT_SIZE
                pen.getTextBounds(it.text, 0, it.text.length, tagSize)
                val fontSize: Float = pen.textSize * box.width() / tagSize.width()

                // adjust the font size so texts are inside the bounding box
                if (fontSize < pen.textSize) pen.textSize = fontSize

                var margin = (box.width() - tagSize.width()) / 2.0F
                if (margin < 0F) margin = 0F
                canvas?.drawText(
                    it.text, box.left + margin,
                    box.top + tagSize.height().times(1F), pen
                )

                holder.unlockCanvasAndPost(canvas)
            }
        }

    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(requireContext())

        cameraProviderFuture.addListener(Runnable {

            val cameraProvider = cameraProviderFuture.get()

            val rotation = viewFinder.display.rotation

            val preview = Preview.Builder()
                .setTargetRotation(rotation)
                .build()
                .also {
                    it.setSurfaceProvider(viewFinder.surfaceProvider)
                }

            val imageAnalyzer = ImageAnalysis.Builder()
                .setTargetRotation(rotation)
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(
                        cameraExecutor,
                        SignLanguageDetector(requireActivity().application as AppApplication, resultOverlay)
                    )
                }


            val cameraSelector =
                CameraSelector.Builder().requireLensFacing(CameraSelector.LENS_FACING_BACK).build()

            try {
                // Unbind use cases before rebinding
                cameraProvider.unbindAll()

                // Bind use cases to camera
                camera = cameraProvider.bindToLifecycle(
                    this, cameraSelector, preview, imageAnalyzer
                )
            } catch (exc: IllegalStateException) {
                Log.e(TAG, "Use case binding failed. This must be running on main thread.", exc)
            }
        }, ContextCompat.getMainExecutor(requireContext()))
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)

        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                viewFinder.post {
                    // Keep track of the display in which this view is attached
                    displayId = viewFinder.display.displayId

                    // Set up the camera and its use cases
                    startCamera()
                }
            } else {
                Toast.makeText(
                    requireContext(),
                    "Permissions not granted by the user.",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

    override fun onStart() {
        super.onStart()



        (requireActivity().application as AppApplication).detector = ObjectDetector.createFromFileAndOptions(
            requireActivity().applicationContext, // the application context
            "model_OD.tflite", // must be same as the filename in assets folder
            (requireActivity().application as AppApplication).options
        )
        Log.d("ONSTART", "Within Onstart ${(requireActivity().application as AppApplication).detector}")
    }

    override fun onStop() {
        super.onStop()
        (requireActivity().application as AppApplication).detector = null
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(
            requireContext(), it
        ) == PackageManager.PERMISSION_GRANTED
    }

    companion object {
        private const val TAG = "CameraXBasic"
        private const val MAX_FONT_SIZE = 96F
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }
}


