package com.example.feelthebook.models.hilt.modules

import com.example.feelthebook.models.retrofit.services.APIAuthService
import com.example.feelthebook.models.retrofit.services.APIConstantsService
import com.example.feelthebook.models.retrofit.services.APILiteratureReadingService
import com.example.feelthebook.models.retrofit.services.APILiteraturesPreviewService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import retrofit2.Retrofit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object ApiServiceModule {
    @Provides
    @Singleton
    fun provideAPIAuthService(retrofit: Retrofit): APIAuthService =
        retrofit.create(APIAuthService::class.java)

    @Provides
    @Singleton
    fun provideAPIConstantsService(retrofit: Retrofit): APIConstantsService =
        retrofit.create(APIConstantsService::class.java)

    @Provides
    @Singleton
    fun provideAPIPreviewLiteraturesService(retrofit: Retrofit): APILiteraturesPreviewService =
        retrofit.create(APILiteraturesPreviewService::class.java)

    @Provides
    @Singleton
    fun provideAPILiteraturesReadingService(retrofit: Retrofit): APILiteratureReadingService =
        retrofit.create(APILiteratureReadingService::class.java)
}

