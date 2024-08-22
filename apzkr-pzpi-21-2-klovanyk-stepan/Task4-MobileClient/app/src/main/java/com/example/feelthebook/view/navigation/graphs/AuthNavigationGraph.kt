package com.example.feelthebook.view.navigation.graphs

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import androidx.navigation.compose.navigation
import com.example.feelthebook.view.composables.complex.LoginForm
import com.example.feelthebook.models.forms.LoginFormData
import com.example.feelthebook.models.navigation.NavDestinations
import com.example.feelthebook.view.composables.complex.RegisterForm
import com.example.feelthebook.models.forms.RegisterFormData
import com.example.feelthebook.view.models.RegisterFormViewModel
import com.example.feelthebook.utils.retrofit.NavDestinationLabels
import com.example.feelthebook.view.models.AuthViewModel

fun NavGraphBuilder.authNavigationGraph(
    navController: NavHostController,
    onLoginSubmit: (LoginFormData) -> Unit,
    onRegisterSubmit: (RegisterFormData) -> Unit,
    onLabelChange: (newLabel: String) -> Unit,
) {
    navigation<NavDestinations.Auth>(
        startDestination = NavDestinations.Auth.Login,
    ) {
        composable<NavDestinations.Auth.Login> {
            onLabelChange(NavDestinationLabels.Login.toString())
            Box(
                Modifier.fillMaxSize(), contentAlignment = Alignment.Center
            ) {
                val parentEntry = remember(it) {
                    navController.getBackStackEntry(NavDestinations.Auth)
                }
                val authViewModel: AuthViewModel = hiltViewModel(parentEntry)
                val initialDataState by authViewModel.initialData.collectAsState()
                LoginForm(initialData = initialDataState.toLoginFormData(), onLoginClick = {
                    onLoginSubmit(it)
                }, onRegisterRedirectClick = {
                    authViewModel.updateInitialData(it)
                    navController.navigate(NavDestinations.Auth.Register)
                })
            }
        }
        composable<NavDestinations.Auth.Register>(
            enterTransition = {
                slideInVertically(animationSpec = tween(2000)) {it}
            }
        ) {
            onLabelChange(NavDestinationLabels.Registration.toString())
            Box(
                Modifier.fillMaxSize(), contentAlignment = Alignment.Center
            ) {
                val parentEntry = remember(it) {
                    navController.getBackStackEntry(NavDestinations.Auth)
                }
                val authViewModel: AuthViewModel = hiltViewModel(parentEntry)
                val registerFormViewModel: RegisterFormViewModel = hiltViewModel()

                val initialDataState by authViewModel.initialData.collectAsState()
                val availableCountries by registerFormViewModel.availableCountries.collectAsState()
                RegisterForm(initialData = initialDataState, onRegisterClick = {
                    authViewModel.updateInitialData(it)
                    onRegisterSubmit(it)
                }, onPeriodicDataSave = {
                    authViewModel.updateInitialData(it)
                }, availableCountries
                )
            }
        }
    }
}
