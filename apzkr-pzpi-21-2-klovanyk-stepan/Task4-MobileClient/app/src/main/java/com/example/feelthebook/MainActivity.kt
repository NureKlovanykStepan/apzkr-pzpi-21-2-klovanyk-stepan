package com.example.feelthebook

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.example.feelthebook.view.theme.FeelTheBookTheme
import dagger.hilt.android.AndroidEntryPoint
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraphBuilder
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import com.example.feelthebook.models.basic.singleton.ErrorDataFlowStorage
import com.example.feelthebook.models.navigation.NavDestinations
import com.example.feelthebook.utils.retrofit.NavDestinationLabels
import com.example.feelthebook.view.composables.elements.FTBTopAppBar
import com.example.feelthebook.view.composables.elements.LiteraturesSwitchingBottomBar
import com.example.feelthebook.view.composables.wrappers.QoLServicesProvider
import com.example.feelthebook.view.models.UserServiceViewModel
import com.example.feelthebook.view.navigation.graphs.authNavigationGraph
import com.example.feelthebook.view.navigation.graphs.literaturesNavigationGraph
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader


@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            FeelTheBookTheme {
                MainAppComposable()
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun MainAppScaffoldPreview() {
    FeelTheBookTheme {
        Scaffold(
            topBar = {
                FTBTopAppBar(
                    titleText = "any text",
                    goBackAvailable = true,
                    onGoBackClick = {},
                    {}
                )
            },
            bottomBar = {
                LiteraturesSwitchingBottomBar(
                    null,
                    {})
            }
        ) {}
    }
}

@Composable
fun MainAppComposable() {
    val userServiceViewModel: UserServiceViewModel = viewModel()
    val errorDataFlowStorage = ErrorDataFlowStorage

    PDFBoxResourceLoader.init(LocalContext.current)

    QoLServicesProvider.WrapContent(
        errorDataFlowStorage = errorDataFlowStorage
    ) {
        val currentUser by userServiceViewModel.currentUser.collectAsState()
        val latestUserFetchingResponse by userServiceViewModel.latestUserFetchingResponseDetails.collectAsState()

        LaunchedEffect(true) {
            userServiceViewModel.coroutineUpdateCurrentUser()
        }

        LabelingProvider {
            val startDestination by remember {
                derivedStateOf {
                    currentUser?.let { NavDestinations.Literatures } ?: NavDestinations.Auth
                }
            }
            val currentBackStackEntry by navController.currentBackStackEntryAsState()

            Scaffold(modifier = Modifier.fillMaxSize(),
                topBar = {
                    GoBackProvider {
                        FTBTopAppBar(
                            titleText = currentLabel,
                            goBackAvailable = canGoBack,
                            onGoBackClick = goBack,
                            onSettingsClick = { navController.navigate(NavDestinations.Settings) }
                        )
                    }
                },
                bottomBar = {
                    LiteraturesSwitchingBottomBar(
                        currentBackStackEntry = currentBackStackEntry,
                        onLiteratureFetchingModeChanged = {
                            navController.navigate(it) {
                                popUpTo(NavDestinations.Literatures.Collections) {
                                    inclusive = true
                                }
                            }
                        }
                    )
                }) { innerPadding ->
                if (latestUserFetchingResponse != null) {
                    NavHost(
                        modifier = Modifier
                            .padding(innerPadding)
                            .fillMaxSize(),
                        navController = navController,
                        startDestination = startDestination
                    ) {
                        authNavigationGraph(
                            navController = navController,
                            onLoginSubmit = { userServiceViewModel.submitLogin(it) },
                            onRegisterSubmit = {
                                userServiceViewModel.createNewUser(it) {
                                    navController.navigate(NavDestinations.Auth) {
                                        popUpTo(NavDestinations.Auth) {
                                            inclusive = true
                                        }
                                    }
                                }
                            },
                            onLabelChange = onLabelChange
                        )
                        literaturesNavigationGraph(
                            navController = navController,
                            onLabelChange = onLabelChange
                        )
                        composable<NavDestinations.Settings> {
                            onLabelChange(NavDestinationLabels.Settings.toString())
                            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.BottomCenter) {
                                Button(
                                    onClick = userServiceViewModel::submitLogout
                                ) {
                                    Row(
                                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Icon(
                                            Icons.AutoMirrored.Filled.ArrowBack,
                                            "log out"
                                        )
                                        Text("Log out")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}






