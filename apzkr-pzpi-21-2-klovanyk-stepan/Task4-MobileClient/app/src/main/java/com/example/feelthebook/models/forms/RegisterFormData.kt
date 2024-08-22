package com.example.feelthebook.models.forms

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class RegisterFormData(
    val email: String,
    val password: String,
    val nickname: String,
    @SerialName("real_name") val realName: String,
    @SerialName("real_surname") val realSurname: String,
    @SerialName("phone_number") val phoneNumber: String,
    @SerialName("country_id") val countryId: Int?,
) {
    fun toLoginFormData(): LoginFormData = LoginFormData(
        email, password
    )

}