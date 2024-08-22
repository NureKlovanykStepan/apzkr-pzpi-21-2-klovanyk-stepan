package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class Country(
    @Json(name = "charcode")
    val charcode: String,
    @Json(name = "code")
    val code: Int,
    @Json(name = "id")
    val id: Int,
    @Json(name = "name")
    val name: String
)