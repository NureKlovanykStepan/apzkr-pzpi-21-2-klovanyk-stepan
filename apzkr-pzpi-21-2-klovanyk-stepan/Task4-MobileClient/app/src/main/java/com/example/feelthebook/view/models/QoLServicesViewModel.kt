package com.example.feelthebook.view.models

import androidx.lifecycle.ViewModel
import com.example.feelthebook.models.basic.TitledTextData
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class QoLServicesViewModel : ViewModel() {
    var _currentLabel: MutableStateFlow<String> = MutableStateFlow("")
    val currentLabel: StateFlow<String> = _currentLabel
    fun setCurrentLabel(label: String) {
        _currentLabel.value = label
    }
}