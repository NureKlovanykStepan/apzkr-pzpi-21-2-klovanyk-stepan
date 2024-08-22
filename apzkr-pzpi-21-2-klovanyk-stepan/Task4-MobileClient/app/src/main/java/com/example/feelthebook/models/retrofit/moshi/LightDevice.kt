package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class LightDevice(
    @Json(name = "details")
    val details: String?,
    @Json(name = "host")
    val host: String,
    @Json(name = "id")
    val id: Int,
    @Json(name = "light_type_name")
    val lightTypeName: String?,
    @Json(name = "port")
    val port: Int,
    @Json(name = "room_id")
    val roomId: Int
)