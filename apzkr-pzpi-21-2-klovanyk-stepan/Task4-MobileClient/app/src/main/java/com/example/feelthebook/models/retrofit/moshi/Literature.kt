package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class Literature(
    @Json(name = "authors")
    val authors: List<Author>,
    @Json(name = "company_id")
    val companyId: Int,
    @Json(name = "description")
    val description: String,
    @Json(name = "editor_email")
    val editorEmail: String,
    @Json(name = "genres")
    val genres: List<Genre>,
    @Json(name = "id")
    val id: Int,
    @Json(name = "min_age")
    val minAge: Int?,
    @Json(name = "name")
    val name: String,
    @Json(name = "page_configs")
    val pageConfigs: List<Any>,
    @Json(name = "pages")
    val pages: Int?,
    @Json(name = "pdf_PATH")
    val pdfPATH: String?,
    @Json(name = "thumbnail_PATH")
    val thumbnailPATH: String?,
    @Json(name = "type")
    val literatureType: LiteratureType,
    @Json(name = "type_name")
    val typeName: String
)