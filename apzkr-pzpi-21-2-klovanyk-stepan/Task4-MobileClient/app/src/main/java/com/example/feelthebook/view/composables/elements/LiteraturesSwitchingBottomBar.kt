package com.example.feelthebook.view.composables.elements

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavBackStackEntry
import androidx.navigation.NavDestination.Companion.hasRoute
import com.example.feelthebook.LiteratureFetchingMode
import com.example.feelthebook.models.navigation.NavDestinations
import com.example.feelthebook.utils.hasAnyRoute

@Composable
fun LiteraturesSwitchingBottomBar(
    currentBackStackEntry: NavBackStackEntry?,
    onLiteratureFetchingModeChanged: (newRoute: Any) -> Unit,
) {
    val allowedRoutes = mapOf(
        LiteratureFetchingMode.All to NavDestinations.Literatures.Collections.All,
        LiteratureFetchingMode.Available to NavDestinations.Literatures.Collections.Available
    )
    if (currentBackStackEntry == null) return
    if (!currentBackStackEntry.destination.hasAnyRoute(allowedRoutes.map { it.value::class })) return

    val currentMode = remember(currentBackStackEntry) {
        allowedRoutes
            .map { currentBackStackEntry.destination.hasRoute(it.value::class) to it.key }
            .toMap()[true]!!
    }
    val selectedColors = ButtonDefaults.buttonColors(
        containerColor = MaterialTheme.colorScheme.primaryContainer,
        contentColor = MaterialTheme.colorScheme.primary
    )

    @Composable
    fun SelectableButton(mode: LiteratureFetchingMode, text: String) =
        when (currentMode == mode) {
            true -> OutlinedButton(
                {},
                colors = selectedColors
            ) { Text(text) }

            false -> Button({ onLiteratureFetchingModeChanged(allowedRoutes[mode]!!) }) { Text(text) }
        }


    BottomAppBar(
        actions = {
            SelectableButton(
                LiteratureFetchingMode.All,
                "All"
            )
            Spacer(Modifier.width(4.dp))
            SelectableButton(
                LiteratureFetchingMode.Available,
                "Available"
            )
        }
    )
}