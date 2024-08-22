package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class Configuration(
    @Json(name = "color")
    val color: Int,
    @Json(name = "color_alter")
    val colorAlter: Int?,
    @Json(name = "color_alter_ms_delta")
    val colorAlterMsDelta: Int?
)