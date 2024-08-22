package com.example.feelthebook.models.navigation

import kotlinx.serialization.Serializable

@Serializable
class NavDestinations() {
    @Serializable
    object Auth {
        @Serializable
        object Login

        @Serializable
        object Register
    }

    @Serializable
    object Literatures {
        @Serializable
        object Collections {
            @Serializable
            object All

            @Serializable
            object Available
        }

        @Serializable
        object Details

        @Serializable
        object Reader
    }

    @Serializable
    object Settings {
        @Serializable
        object Profile
    }

    @Serializable
    object Home
}