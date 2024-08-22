package com.example.feelthebook.view.composables.complex

import android.widget.Toast
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.text.input.TextFieldState
import androidx.compose.foundation.text.input.rememberTextFieldState
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.feelthebook.models.forms.RegisterFormData
import com.example.feelthebook.models.retrofit.moshi.Country
import com.example.feelthebook.view.composables.elements.PrettyBasicTextField
import com.example.feelthebook.view.theme.FeelTheBookTheme
import kotlinx.coroutines.delay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RegisterForm(
    initialData: RegisterFormData?,
    onRegisterClick: (RegisterFormData) -> Unit,
    onPeriodicDataSave: (RegisterFormData) -> Unit,
    availableCountries: Map<Int, Country>,
) {
    val emailTextFieldState = rememberTextFieldState()
    val passwordTextFieldState = rememberTextFieldState()
    val nicknameTextFieldState = rememberTextFieldState()
    val realNameTextFieldState = rememberTextFieldState()
    val realSurnameTextFieldState = rememberTextFieldState()
    val phoneNumberTextFieldState = rememberTextFieldState()
    var selectedCountryId by remember { mutableStateOf(-1) }

    val context = LocalContext.current
    var doSkipSave by remember { mutableStateOf(true) }

    fun createData() = RegisterFormData(
        email = emailTextFieldState.text.toString(),
        password = passwordTextFieldState.text.toString(),
        nickname = nicknameTextFieldState.text.toString(),
        realName = realNameTextFieldState.text.toString(),
        realSurname = realSurnameTextFieldState.text.toString(),
        phoneNumber = phoneNumberTextFieldState.text.toString(), countryId = selectedCountryId
    )

    LaunchedEffect(
        emailTextFieldState, passwordTextFieldState, nicknameTextFieldState, realNameTextFieldState,
        realSurnameTextFieldState, phoneNumberTextFieldState, selectedCountryId
    ) {
        if (doSkipSave) {
            doSkipSave = false
            return@LaunchedEffect
        }
        delay(1000)
        onPeriodicDataSave(
            createData()
        )
        Toast
            .makeText(
                context, "Data saved", Toast.LENGTH_SHORT
            )
            .show()
    }

    LaunchedEffect(initialData) {
        doSkipSave = true
        emailTextFieldState.edit {
            this.replace(
                0, this.length, initialData?.email ?: ""
            )
        }
        passwordTextFieldState.edit {
            this.replace(
                0, this.length, initialData?.password ?: ""
            )
        }
        nicknameTextFieldState.edit {
            this.replace(
                0, this.length, initialData?.nickname ?: ""
            )
        }
        realNameTextFieldState.edit {
            this.replace(
                0, this.length, initialData?.realName ?: ""
            )
        }
        realSurnameTextFieldState.edit {
            this.replace(
                0, this.length, initialData?.realSurname ?: ""
            )
        }
        phoneNumberTextFieldState.edit {
            this.replace(
                0, this.length, initialData?.phoneNumber ?: ""
            )
        }

        if (initialData?.countryId != null) {
            selectedCountryId = initialData.countryId
        }
    }

    val textFields: List<Pair<TextFieldState, String>> = listOf(
        emailTextFieldState to "Email",
        passwordTextFieldState to "Password",
        nicknameTextFieldState to "Nickname",
        realNameTextFieldState to "Real Name",
        realSurnameTextFieldState to "Real Surname",
    )

    Box(Modifier.fillMaxWidth()) {
        Column (
            Modifier.padding(
                16.dp, 4.dp
            ), verticalArrangement = Arrangement.spacedBy(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            textFields.map {
                val (textFieldState, label) = it
                val interactionSource = remember { MutableInteractionSource() }
                ElevatedCard {
                    PrettyBasicTextField(
                        textFieldState = textFieldState, modifier = Modifier
                            .fillMaxWidth()
                            .padding(4.dp), label = { Text(label) },
                        interactionSource = interactionSource
                    )
                }
            }
            var expanded by remember { mutableStateOf(false) }
            ElevatedCard {
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    modifier = Modifier.padding(4.dp),
                    onExpandedChange = { expanded = it },
                ) {
                    OutlinedTextField(value = availableCountries[selectedCountryId]?.name ?: "",
                        readOnly = true, label = { Text("Country") },
                        shape = MaterialTheme.shapes.small, trailingIcon = {
                            ExposedDropdownMenuDefaults.TrailingIcon(
                                expanded = expanded
                            )
                        }, onValueChange = { }, modifier = Modifier
                            .menuAnchor()
                            .fillMaxWidth()
                    )
                    ExposedDropdownMenu(
                        expanded = expanded, onDismissRequest = { expanded = false }) {
                        availableCountries.entries
                            .sortedBy {
                                it.value.name
                            }
                            .forEach {
                                DropdownMenuItem(text = {
                                    Text(buildAnnotatedString {
                                        append(it.value.name)
                                        append(" (+")
                                        append(it.value.code.toString())
                                        append(")")
                                    })
                                }, onClick = {
                                    selectedCountryId = it.key
                                    expanded = false
                                })
                            }
                    }
                }
            }

            val interactionSource = remember { MutableInteractionSource() }
            ElevatedCard {
                PrettyBasicTextField(
                    textFieldState = phoneNumberTextFieldState, modifier = Modifier
                        .fillMaxWidth()
                        .padding(4.dp), label = { Text("Phone number") },
                    interactionSource = interactionSource
                )
            }
            Button(
                onClick = {
                    onRegisterClick(
                        createData()
                    )
                }, Modifier.padding(0.dp)
            ) {
                Text(
                    "Register", Modifier.padding(
                        16.dp, 0.dp
                    ), style = MaterialTheme.typography.titleLarge
                )
            }
        }
    }
}

@Preview
@Composable
fun RegisterFormPreview() {
    FeelTheBookTheme {
        RegisterForm(initialData = null, onRegisterClick = {}, onPeriodicDataSave = {},
            availableCountries = listOf(
                Country(
                    charcode = "UK", code = 380, name = "Ukraine", id = 1
                ), Country(
                    charcode = "US", code = 1, name = "USA", id = 2
                ), Country(
                    charcode = "PO", code = 48, name = "Poland", id = 3
                )
            ).associateBy { it.id })
    }
}