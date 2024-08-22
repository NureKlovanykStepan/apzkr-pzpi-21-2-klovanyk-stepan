package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ReadingLiterature(
    @Json(name = "id")
    val id: Int,
    @Json(name = "page_configs")
    val pageConfigs: List<PageConfig>
)