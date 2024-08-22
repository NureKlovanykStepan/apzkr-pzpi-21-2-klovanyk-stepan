package com.example.feelthebook.view.models

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.feelthebook.models.retrofit.moshi.Country
import com.example.feelthebook.models.retrofit.services.APIConstantsService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class RegisterFormViewModel @Inject constructor(
    apiConstantsService: APIConstantsService,
) : ViewModel() {
    private var _countries: MutableStateFlow<Map<Int, Country>> = MutableStateFlow(emptyMap())
    val availableCountries: StateFlow<Map<Int, Country>> = _countries

    init {
        viewModelScope.launch {
            _countries.value = apiConstantsService
                .getAvailableCountries()
                .body()!!
                .associateBy { it.id }
        }
    }
}