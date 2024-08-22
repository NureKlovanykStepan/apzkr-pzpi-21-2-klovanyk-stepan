package com.example.feelthebook.models.forms

import kotlinx.serialization.Serializable

@Serializable
data class LoginFormData(val email: String, val password: String) {
    fun toRegisterFormData(): RegisterFormData = RegisterFormData(
        email, password, "", "", "", "", null
    )
}