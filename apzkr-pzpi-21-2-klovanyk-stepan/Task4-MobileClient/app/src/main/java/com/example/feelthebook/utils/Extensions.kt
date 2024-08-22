package com.example.feelthebook.utils

import androidx.navigation.NavDestination
import androidx.navigation.NavDestination.Companion.hasRoute
import com.example.feelthebook.models.basic.singleton.ErrorDataFlowStorage
import com.example.feelthebook.models.basic.TitledTextData
import com.example.feelthebook.models.retrofit.moshi.Literature
import com.squareup.moshi.Moshi
import retrofit2.Response
import kotlin.reflect.KClass

//suspend fun <T> Response<T>.emitErrorFromResponseFailure(title: String) {
//    ErrorDataFlowStorage.emitError(
//        TitledTextData(
//            title = "$title (${code()})",
//            message = errorBody()?.string() ?: "Unknown error"
//        )
//    )
//}

suspend fun <T> Response<T>.emitErrorFromResponseFailure(title: String): String =
    with(errorBody()?.string()) {
        ErrorDataFlowStorage.emitError(
            TitledTextData(
                title = "$title (${code()})",
                message = this ?: "Unknown error"
            )
        )
        return this?:""
    }


fun <T : Any> NavDestination.hasAnyRoute(routes: List<KClass<out T>>) = routes.any { hasRoute(it) }
fun mock_literature(id: Int = 1): Literature {
    val mock_data = """
        {
        "authors": [
            {
                "id": 2,
                "name": "Vasya",
                "pseudonym": "0",
                "surname": "Makimus"
            },
            {
                "id": 296,
                "name": null,
                "pseudonym": "Author-145",
                "surname": null
            }
        ],
        "company_id": 1,
        "description": "Hori tries to seem like an ordinary high school student, while in fact she devotes all her time to taking care of the house. The girl has to take the place of her younger brother in the family, cleaning, laundry and other household chores. One day she meets a man who, just like her, tries not to reveal his true personality at school: Miyamura, a silent guy with glasses. Now the two of them have someone to share and reveal their true selves without fear of being found out at school. ",
        "editor_email": "llm@example.com",
        "genres": [
            {
                "name": "Apocalypse"
            },
            {
                "name": "Abc"
            },
            {
                "name": "defer"
            }
        ],
        "id": $id,
        "min_age": 21,
        "name": "Name-27486",
        "page_configs": [],
        "pages": 13,
        "pdf_PATH": "null",
        "thumbnail_PATH": "null",
        "type": {
            "name": "Novel"
        },
        "type_name": "Novel"
    }
    """.trimIndent()
    val moshi = Moshi.Builder()
        .build()
    val adapter = moshi.adapter(Literature::class.java)
    return adapter.fromJson(mock_data)!!
}