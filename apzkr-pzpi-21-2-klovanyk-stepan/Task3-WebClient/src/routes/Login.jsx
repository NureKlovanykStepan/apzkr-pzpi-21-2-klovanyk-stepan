import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {API} from "../App";
import DatePicker from "react-datepicker";

function Login({onLogin}) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();

        await API.post('/auth/login',{},{
            auth: {
                username: email,
                password: password
            },
            withCredentials: true
        }).then((response) => {
            onLogin().then(
                () => navigate('/')
            )
        }).catch((error) => {
            console.log(error.response);
            if (error.response.status === 401) {
                window.alert(error.response.data)
            }
        })
    };

    return (
        <div className="container">
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
                <div className="form-group">
                    <label htmlFor="email">Email:</label>
                    <input
                        type="email"
                        className="form-control"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password">Password:</label>
                    <input
                        type="password"
                        className="form-control"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
                <button type="submit" className="btn btn-primary">Login</button>
            </form>
        </div>
    );
}

export default Login;