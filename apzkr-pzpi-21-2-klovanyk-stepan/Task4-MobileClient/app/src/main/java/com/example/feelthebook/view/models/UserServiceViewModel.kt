package com.example.feelthebook.view.models

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.feelthebook.utils.emitErrorFromResponseFailure
import com.example.feelthebook.models.forms.LoginFormData
import com.example.feelthebook.models.forms.RegisterFormData
import com.example.feelthebook.models.retrofit.moshi.User
import com.example.feelthebook.models.retrofit.services.APIAuthService
import com.example.feelthebook.utils.auth.BasicAuthCredentialsEncoder
import com.example.feelthebook.utils.retrofit.toFailedCodeAndResponse
import com.example.feelthebook.utils.retrofit.toSuccessCodeAndResponse
import com.squareup.moshi.Moshi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import javax.inject.Inject

@HiltViewModel
class UserServiceViewModel @Inject constructor(
    private val apiAuthService: APIAuthService,
    private val moshi: Moshi,
) : ViewModel() {
    private var _currentUser = MutableStateFlow<User?>(null)
    private var _latestUserFetchingResponseDetails: MutableStateFlow<Pair<Int, String>?> =
        MutableStateFlow(null)
    val currentUser: StateFlow<User?> = _currentUser
    val latestUserFetchingResponseDetails: StateFlow<Pair<Int, String>?> =
        _latestUserFetchingResponseDetails

    fun submitLogin(
        loginFormData: LoginFormData,
    ) = viewModelScope.launch {
        apiAuthService
            .login(
                BasicAuthCredentialsEncoder().encode(
                    loginFormData.email,
                    loginFormData.password
                )
            )
            .takeIf { !it.isSuccessful }
            ?.run { emitErrorFromResponseFailure("Login failed") }
            ?: coroutineUpdateCurrentUser()
    }


    suspend fun coroutineUpdateCurrentUser() {
        apiAuthService
            .getCurrentUser()
            .apply {
                _currentUser.emit(
                    takeIf { isSuccessful }?.body()
                        ?: takeIf { code() != 401 }
                            ?.apply { emitErrorFromResponseFailure("Failed to load user") }
                            .let { null }
                )
            }
            .run {
                _latestUserFetchingResponseDetails.emit(
                    toFailedCodeAndResponse() ?: toSuccessCodeAndResponse()!!.let {
                        it.first to moshi
                            .adapter(User::class.java)
                            .toJson(it.second)
                    })
            }
    }

    fun submitLogout() = viewModelScope.launch {
        apiAuthService.logout()
            .takeIf { !it.isSuccessful }
            ?.run { emitErrorFromResponseFailure("Logout failed") }
            ?: _currentUser.emit(null)
    }

    fun createNewUser(registerFormData: RegisterFormData, onRegisterSuccess: () -> Unit) {
        viewModelScope.launch {
            apiAuthService
                .register(Json.encodeToString(registerFormData))
                .run {
                    takeIf { !isSuccessful }?.emitErrorFromResponseFailure("Register failed")
                        ?: onRegisterSuccess()
                }
        }
    }
}