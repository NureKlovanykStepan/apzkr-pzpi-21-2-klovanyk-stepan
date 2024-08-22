package com.example.feelthebook.utils.retrofit

enum class NavDestinationLabels {
    Login,
    Registration,
    All_Literatures,
    Available_Literatures,
    Literatures_Details,
    Settings,
    Reader;

    private fun formattedName() = name.replace(
        "_", " "
    )

    override fun toString(): String {
        return formattedName()
    }

}