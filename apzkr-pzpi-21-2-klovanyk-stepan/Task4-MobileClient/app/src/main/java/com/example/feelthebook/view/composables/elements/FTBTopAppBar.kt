package com.example.feelthebook.view.composables.elements

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.example.feelthebook.view.theme.FeelTheBookTheme

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FTBTopAppBar(
    titleText: String,
    goBackAvailable: Boolean,
    onGoBackClick: () -> Unit,
    onSettingsClick: () -> Unit,
) {
    return CenterAlignedTopAppBar(
        title = { Text(titleText) },
        navigationIcon = {
            if (goBackAvailable) IconButton(onClick = onGoBackClick) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                    contentDescription = "go back"
                )
            }
        }, colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainer
        ),
        actions = {
            IconButton(onClick = onSettingsClick) {
                Icon(Icons.Default.Settings, "settings")
            }
        }
    )
}

@Preview
@Composable
fun ScaffoldWithTopBarPreview() {
    FeelTheBookTheme {
        Scaffold(modifier = Modifier.fillMaxSize(), topBar = {
            FTBTopAppBar(titleText = "Test", goBackAvailable = true, onGoBackClick = {}, {})
        }) {}
    }
}

@Preview
@Composable
fun FTBTopAppBarPreview() {
    FeelTheBookTheme {
        FTBTopAppBar(titleText = "Test", goBackAvailable = true, onGoBackClick = {}, {})
    }
}