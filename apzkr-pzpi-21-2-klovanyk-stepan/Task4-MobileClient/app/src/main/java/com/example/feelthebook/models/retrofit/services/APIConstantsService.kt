package com.example.feelthebook.models.retrofit.services

import com.example.feelthebook.models.retrofit.moshi.Author
import com.example.feelthebook.models.retrofit.moshi.Country
import com.example.feelthebook.models.retrofit.moshi.Genre
import com.example.feelthebook.models.retrofit.moshi.LiteratureType
import retrofit2.Response
import retrofit2.http.GET

interface APIConstantsService {
    @GET("countries/?I=country")
    suspend fun getAvailableCountries(): Response<List<Country>?>

    @GET("genres/?I=genre")
    suspend fun getAvailableGenres(): Response<List<Genre>>

    @GET("authors/?I=author")
    suspend fun getAvailableAuthors(): Response<List<Author>>

    @GET("literature_types/?I=literature_type")
    suspend fun getAvailableLiteratureTypes(): Response<List<LiteratureType>>
}