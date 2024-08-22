package com.example.feelthebook.models.retrofit.services

import com.example.feelthebook.models.retrofit.moshi.Literature
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface APILiteraturesPreviewService {
    @GET("literatures/?I=literature,genre,author,literature_type")
    suspend fun getAllLiteratures(
        @Query("join") join: List<String>,
        @Query("filter") filter: List<String>,
        @Query("max") maxCount: Int,
        @Query("offset") offset: Int,
        @Query("having_genre") havingGenre: List<String>
    ): Response<List<Literature>>

    @GET("literatures/available/?I=literature,genre,author,literature_type")
    suspend fun getAvailableLiteratures(
        @Query("join") join: List<String>,
        @Query("filter") filter: List<String>,
        @Query("max") maxCount: Int,
        @Query("offset") offset: Int,
        @Query("having_genre") havingGenre: List<String>
    ): Response<List<Literature>>

    @GET("literatures/{id}/thumbnail")
    suspend fun getThumbnail (
        @Path("id") id: Int,
        @Query("width") width: Int,
    ): Response<ResponseBody>
}