package com.example.feelthebook.models.hilt.modules

import android.content.Context
import android.util.Log
import androidx.core.content.ContextCompat
import com.example.feelthebook.utils.auth.ModifiedPersistentCookieJar
import com.example.feelthebook.R
import com.franmontiel.persistentcookiejar.PersistentCookieJar
import com.franmontiel.persistentcookiejar.cache.SetCookieCache
import com.franmontiel.persistentcookiejar.persistence.SharedPrefsCookiePersistor
import com.squareup.moshi.Moshi
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Protocol
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.converter.scalars.ScalarsConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object RetrofitBaseModule {
    @Provides
    @Singleton
    fun provideBaseUrl(@ApplicationContext context: Context): String = ContextCompat.getString(
        context, R.string.api_url
    )

    @Provides
    @Singleton
    fun provideLoggingInterceptor(): HttpLoggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    @Provides
    @Singleton
    fun provideCookieJar(@ApplicationContext context: Context): PersistentCookieJar =
        ModifiedPersistentCookieJar(
            SetCookieCache(), SharedPrefsCookiePersistor(context)
        )

    @Provides
    @Singleton
    fun provideClient(cookieJar: PersistentCookieJar, loggingInterceptor: HttpLoggingInterceptor) =
        OkHttpClient
            .Builder()
            .protocols(listOf(Protocol.HTTP_1_1))
            .readTimeout(40, TimeUnit.SECONDS)
            .connectTimeout(40, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .addInterceptor(RetryInterceptor(9))
            .addInterceptor(loggingInterceptor)
            .cookieJar(cookieJar)
            .build()

    @Provides
    @Singleton
    fun provideMoshi(): Moshi = Moshi
        .Builder()
        .build()

    @Provides
    @Singleton
    fun provideRetrofitBuilder(client: OkHttpClient, moshi: Moshi): Retrofit.Builder =
        Retrofit
            .Builder()
            .client(client)
            .addConverterFactory(ScalarsConverterFactory.create())
            .addConverterFactory(MoshiConverterFactory.create(moshi))


    @Provides
    @Singleton
    fun provideApiRetrofit(
        baseUrl: String, retrofitBuilder: Retrofit.Builder,
    ): Retrofit =
        retrofitBuilder
            .baseUrl(baseUrl)
            .build()
}



class RetryInterceptor(private val maxRetries: Int) : Interceptor {
    @Throws(IOException::class)
    override fun intercept(chain: Interceptor.Chain): Response {
        var request = chain.request()
        var retryCount = 0
        while (true) {
            try {
                return chain.proceed(request)
            } catch (e: IOException) {
                if (retryCount >= maxRetries) {
                    throw e
                }
                retryCount++
                // Optionally, add a delay between retries
                Thread.sleep(2000)
            }
        }
    }
}