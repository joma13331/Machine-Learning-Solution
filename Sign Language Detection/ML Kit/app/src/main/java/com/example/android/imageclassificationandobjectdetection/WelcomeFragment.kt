package com.example.android.imageclassificationandobjectdetection

import android.os.Bundle
import androidx.fragment.app.Fragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.navigation.fragment.findNavController
import com.example.android.imageclassificationandobjectdetection.databinding.FragmentWelcomeBinding


class WelcomeFragment : Fragment() {


    private lateinit var binding:FragmentWelcomeBinding

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {

        binding = FragmentWelcomeBinding.inflate(inflater, container, false)

        binding.imageClassification.setOnClickListener {
            findNavController().navigate(R.id.imageClassificationFragment)
        }

        binding.objectDetectionImage.setOnClickListener {
            findNavController().navigate(R.id.objectDetectionImageFragment)
        }

        binding.liveObjectDetection.setOnClickListener {
            findNavController().navigate(R.id.liveObjectDetectionFragment)
        }
        // Inflate the layout for this fragment
        return binding.root
    }


}