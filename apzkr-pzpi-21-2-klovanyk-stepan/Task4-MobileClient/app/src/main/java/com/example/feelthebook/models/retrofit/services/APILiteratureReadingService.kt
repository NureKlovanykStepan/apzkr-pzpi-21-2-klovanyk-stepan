package com.example.feelthebook.models.retrofit.services

import com.example.feelthebook.models.retrofit.moshi.LightDevice
import com.example.feelthebook.models.retrofit.moshi.ReadingLiterature
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Headers
import retrofit2.http.Path

interface APILiteratureReadingService {
    @GET("literatures/{id}/pdf")
    @Headers(
        "Connection: close"
    )
    suspend fun getLiteraturePDF(
        @Path("id") id: Int
    ): Response<ResponseBody>

    @GET("literatures/{id}?I=literature.id,literature_page_config")
    suspend fun getReadingLiterature(
        @Path("id") id: Int
    ): Response<ReadingLiterature>

    @GET("light_devices/first_accessible?I=light_device")
    suspend fun getFirstAvailableLightDevices(): Response<List<LightDevice>>
}