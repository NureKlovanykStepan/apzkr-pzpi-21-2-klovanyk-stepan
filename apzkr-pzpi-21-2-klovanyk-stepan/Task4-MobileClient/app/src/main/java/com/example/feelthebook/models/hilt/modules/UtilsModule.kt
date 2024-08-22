package com.example.feelthebook.models.hilt.modules

import com.example.feelthebook.models.basic.singleton.ThumbnailsCache
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object UtilsModule {
    @Provides
    @Singleton
    fun provideThumbnailsCache(): ThumbnailsCache = ThumbnailsCache
}