package com.example.feelthebook.models.basic.singleton

import com.example.feelthebook.models.basic.TitledTextData
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

object ErrorDataFlowStorage {
    private var _errorDataFlow: MutableStateFlow<TitledTextData?> = MutableStateFlow(null)
    val errorDataFlow: StateFlow<TitledTextData?> = _errorDataFlow

    suspend fun emitError(error: TitledTextData) {
        _errorDataFlow.emit(error)
    }
}