package com.example.feelthebook.models.retrofit.moshi


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class User(
    @Json(name = "country_id")
    val countryId: Int,
    @Json(name = "email")
    val email: String,
    @Json(name = "employee")
    val employee: Employee?,
    @Json(name = "nickname")
    val nickname: String,
    @Json(name = "password_hash")
    val passwordHash: String,
    @Json(name = "phone_number")
    val phoneNumber: String,
    @Json(name = "real_name")
    val realName: String,
    @Json(name = "real_surname")
    val realSurname: String
)