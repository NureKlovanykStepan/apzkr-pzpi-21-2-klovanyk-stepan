package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class Employee(
    @Json(name = "booking_manager")
    val bookingManager: Boolean,
    @Json(name = "establishment_id")
    val establishmentId: Int,
    @Json(name = "head_manager")
    val headManager: Boolean,
    @Json(name = "iot_manager")
    val iotManager: Boolean,
    @Json(name = "literature_manager")
    val literatureManager: Boolean,
    @Json(name = "user_email")
    val userEmail: String
)