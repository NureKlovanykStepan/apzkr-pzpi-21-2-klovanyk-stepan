package com.example.feelthebook.models.retrofit.services

import com.example.feelthebook.models.retrofit.moshi.User
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Headers
import retrofit2.http.POST

interface APIAuthService {
    @Headers("Content-Type: application/json")
    @POST("auth/login")
    suspend fun login(
        @Header("Authorization") encodedCredentials: String,
    ): Response<String?>

    @GET("auth/logout")
    suspend fun logout(): Response<String?>

    @GET("users/self?I=user,employee")
    suspend fun getCurrentUser(): Response<User?>

    @POST("users")
    @Headers("Content-Type: application/json")
    suspend fun register(
        @Body userData: String,
    ): Response<String?>
}