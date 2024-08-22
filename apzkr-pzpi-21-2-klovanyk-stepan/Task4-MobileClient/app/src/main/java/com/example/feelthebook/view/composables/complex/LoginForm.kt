package com.example.feelthebook.view.composables.complex

import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.input.rememberTextFieldState
import androidx.compose.material3.Button
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.feelthebook.models.forms.LoginFormData
import com.example.feelthebook.view.composables.elements.PrettyBasicTextField
import com.example.feelthebook.view.theme.FeelTheBookTheme

@Composable
fun LoginForm(
    initialData: LoginFormData?,
    onLoginClick: (LoginFormData) -> Unit,
    onRegisterRedirectClick: (LoginFormData) -> Unit,
) {
    val emailTextFieldState = rememberTextFieldState()
    val passwordTextFieldState = rememberTextFieldState()

    LaunchedEffect(initialData) {
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
    }

    val emailInteractionSource = remember { MutableInteractionSource() }
    val passwordInteractionSource = remember { MutableInteractionSource() }

    return Surface(
        Modifier.fillMaxWidth(),
    ) {
        Column(
            Modifier.padding(
                16.dp, 4.dp
            ), verticalArrangement = Arrangement.spacedBy(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            ElevatedCard() {
                PrettyBasicTextField(textFieldState = emailTextFieldState,
                    interactionSource = emailInteractionSource, modifier = Modifier
                        .fillMaxWidth()
                        .padding(4.dp), label = { Text("Email") })
            }
            ElevatedCard {
                PrettyBasicTextField(textFieldState = passwordTextFieldState,
                    interactionSource = passwordInteractionSource, modifier = Modifier
                        .fillMaxWidth()
                        .padding(4.dp), label = { Text("Password") })
            }
            Row(
                Modifier
                    .padding(
                        8.dp, 4.dp
                    )
                    .height(IntrinsicSize.Min)
            ) {
                Text(
                    "Do not have an account? ",
                )
                Text(
                    "Register", style = LocalTextStyle.current.copy(
                        color = MaterialTheme.colorScheme.primary,
                        textDecoration = TextDecoration.Underline
                    ), modifier = Modifier.clickable(onClick = {
                        onRegisterRedirectClick(
                            LoginFormData(
                                email = emailTextFieldState.text.toString(),
                                password = passwordTextFieldState.text.toString()
                            )
                        )
                    })
                )
            }
            Button(
                onClick = {
                    onLoginClick(
                        LoginFormData(
                            email = emailTextFieldState.text.toString(),
                            password = passwordTextFieldState.text.toString()
                        )
                    )
                }, Modifier.padding(0.dp)
            ) {
                Text(
                    "Log In", Modifier.padding(
                        16.dp, 0.dp
                    ), style = MaterialTheme.typography.titleLarge
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun LoginFormPreview() {
    FeelTheBookTheme {
        LoginForm(null, {}, {})
    }
}