package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class PageConfig(
    @Json(name = "configuration")
    val configuration: Configuration,
    @Json(name = "id")
    val id: Int,
    @Json(name = "light_type_name")
    val lightTypeName: String,
    @Json(name = "literature_id")
    val literatureId: Int,
    @Json(name = "page_number")
    val pageNumber: Int
)