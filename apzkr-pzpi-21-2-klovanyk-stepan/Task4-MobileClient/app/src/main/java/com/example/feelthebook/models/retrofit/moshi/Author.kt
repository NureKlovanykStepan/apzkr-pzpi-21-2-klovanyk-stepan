package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class Author(
    @Json(name = "id")
    val id: Int,
    @Json(name = "name")
    val name: String?,
    @Json(name = "pseudonym")
    val pseudonym: String,
    @Json(name = "surname")
    val surname: String?
)