package com.example.feelthebook.view.models

import androidx.lifecycle.ViewModel
import com.example.feelthebook.models.forms.LoginFormData
import com.example.feelthebook.models.forms.RegisterFormData
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class AuthViewModel : ViewModel() {
    var _initialData: MutableStateFlow<RegisterFormData> = MutableStateFlow(
        RegisterFormData(
            "",
            "",
            "",
            "",
            "",
            "",
            null,
        )
    )
    val initialData: StateFlow<RegisterFormData> = _initialData

    fun updateInitialData(initialData: RegisterFormData) {
        _initialData.value = initialData
    }

    fun updateInitialData(initialData: LoginFormData) {
        _initialData.value = _initialData.value.copy(
            email = initialData.email, password = initialData.password
        )
    }

}