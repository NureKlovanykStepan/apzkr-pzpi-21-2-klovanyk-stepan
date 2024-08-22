package com.example.feelthebook.view.composables.wrappers

import android.util.Log
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.example.feelthebook.models.basic.singleton.ErrorDataFlowStorage
import com.example.feelthebook.models.basic.TitledTextData
import com.example.feelthebook.view.composables.elements.ErrorDialog
import com.example.feelthebook.view.models.QoLServicesViewModel
import kotlinx.coroutines.delay

class QoLServicesProvider private constructor(
    val navController: NavHostController,
    private val currentLabel: String,
    private val onLabelChange: (newLabel: String) -> Unit = {},
) {
    companion object {
        @Composable
        fun WrapContent(
            errorDataFlowStorage: ErrorDataFlowStorage = ErrorDataFlowStorage,
            content: @Composable QoLServicesProvider.() -> Unit,
        ) {
            val navController = rememberNavController()
            val qoLServicesViewModel: QoLServicesViewModel = viewModel()
            val currentLabel by qoLServicesViewModel.currentLabel.collectAsState()
            var errorData by remember {
                mutableStateOf<TitledTextData?>(null)
            }

            LaunchedEffect(true) {
                errorDataFlowStorage.errorDataFlow.collect {
                    Log.d("viewchangedebug", "$it")
                    errorData = it
                    while (errorData != null) {
                        delay(1000)
                    }
                }
            }

            if (errorData != null) {
                ErrorDialog(
                    titleText = errorData!!.title,
                    message = errorData!!.message,
                ) {
                    errorData = null
                }
            }

            val provider =
                QoLServicesProvider(navController = navController,
                    currentLabel = currentLabel,
                    onLabelChange = { qoLServicesViewModel.setCurrentLabel(it) })
            return provider.content()
        }
    }

    data class GoBackService(
        val canGoBack: Boolean,
        val goBack: () -> Unit,
    )

    @Composable
    fun GoBackProvider(content: @Composable GoBackService.() -> Unit) {
        val currentBackStackEntry by navController.currentBackStackEntryAsState()
        val canPop by remember {
            derivedStateOf {
                currentBackStackEntry != null && navController.previousBackStackEntry != null
            }
        }
        return GoBackService(canPop) { navController.popBackStack() }.content()
    }

    data class LabelingService(
        val currentLabel: String,
        val onLabelChange: (newLabel: String) -> Unit,
    )

    @Composable
    fun LabelingProvider(content: @Composable LabelingService.() -> Unit) {
        return LabelingService(
            currentLabel,
            onLabelChange
        ).content()
    }
}