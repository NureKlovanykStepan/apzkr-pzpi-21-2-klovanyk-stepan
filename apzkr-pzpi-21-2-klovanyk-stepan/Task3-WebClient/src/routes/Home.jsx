import React from 'react';
function Home({employee}) {
    return (<div className="container">
            <h1 className="text-center">Welcome</h1>
            {employee && (<div>
                <p>Hello, {employee.user.nickname}!</p>
            </div>)}
        </div>);
}

export default Home;