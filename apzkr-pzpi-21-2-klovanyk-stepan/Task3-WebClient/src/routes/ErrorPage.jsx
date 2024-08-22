import React from "react";

function ErrorPage({message}) {
    return (
        <div>
            <h4>This page is shown on unexpected errors</h4>
            <h1>{message}</h1>
        </div>
    );
}

export default ErrorPage