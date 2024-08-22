import React, {useState, useEffect} from 'react';
import {BrowserRouter, Routes, Route, Navigate, useNavigate} from 'react-router-dom';
import axios from 'axios';
import Home from './routes/Home';
import Login from './routes/Login';
import User from './models/User';
import ErrorPage from "./routes/ErrorPage";
import Company from "./models/Company";
import company from "./models/Company";
import Bookings from "./routes/Bookings";
import NavHeader from "./components/NavHeader";
import Employees from "./routes/Employees";
import CompaniesAndEstablishments from "./routes/CompaniesAndEstablishments";
import IoT from "./routes/IoT";
import Literatures from "./routes/Literatures";

export const API = axios.create({
    baseURL: 'http://localhost:8888/api/v2', withCredentials: true
});

class CompanyManager {
    constructor(employee, companySetter) {
        return new Promise(async (resolve) => {
            this._companySetter = companySetter;
            this.selectedCompany = employee.establishment.company;
            companySetter(this.selectedCompany);
            if (!this.selectedCompany.global_access_company) this.availableCompanies = [this.selectedCompany];
            else await API.get('/companies/accessible?I=company').then((response) => {
                this.availableCompanies = response.data;
            })
            resolve(this);
        })
    }

    get asOptions() {
        return this.availableCompanies.map(
            company => ({value: company.id, label: company.name})
        )
    }

    changeCompany(companyId) {
        this.selectedCompany = this.availableCompanies.find(
            company => company.id === companyId
        );
        this._companySetter(this.selectedCompany);
    }
}

function App() {
    const [employee, setEmployee] = useState(null);
    const [isUserReady, setIsUserReady] = useState(false);
    const [isUserEmployee, setIsUserEmployee] = useState(false);
    const [companyManager, setCompanyManager] = useState(null);
    const [currentCompany, setCurrentCompany] = useState(null);

    const loadEmployee = async () => {
        setIsUserReady(false);
        await API.get('/users/self?I=employee,user,establishment,company', {
            withCredentials: true
        }).then((response) => {
            const user = new User(response.data);
            if (user && user.employee !== null) {
                setEmployee(user.employee)
            } else {
                window.alert("You are not an employee");
                API.get('/auth/logout').catch((error) => {})
            }
            setIsUserEmployee(!!user.employee);
        }).catch((error) => {
            console.log(error.response ? error.response : error);
        }).finally(() => {
            setIsUserReady(true);
        })
    }

    useEffect(() => {
        (async () => {
            setCompanyManager(employee ? await new CompanyManager(employee, setCurrentCompany) : null);
        })()
    }, [employee]);

    useEffect(() => {
        (async () => {
            await loadEmployee();
        })()
    }, []);

    const handleLogout = async () => {
        setIsUserReady(false);
        setEmployee(null);
        setCompanyManager(null);
        API.get('auth/logout', {
            withCredentials: true
        }).catch((error) => {
            console.log(error.response);
        }).finally(() => {
            setIsUserReady(true);
        });
    };

    if (!isUserReady) {
        return (<div>Loading...</div>);
    }

    return (<BrowserRouter>
        <Routes>
            <Route path="/login" element={<Login onLogin={loadEmployee}/>}/>
            {employee && isUserEmployee ? (
                <Route path="/" element={<NavHeader employee={employee} onLogout={handleLogout} companyManager={companyManager}/>}>
                    <Route path="/" element={<Home employee={employee}/>}></Route>
                    <Route path="/bookings" element={<Bookings employee={employee} company={currentCompany}/>}/>
                    <Route path="/employees" element={<Employees employee={employee} company={currentCompany} loadEmployee={loadEmployee}/>}/>
                    <Route path="/companies_establishments" element={<CompaniesAndEstablishments employee={employee} company={currentCompany} loadEmployee={loadEmployee}/>}/>
                    <Route path="/iot_management" element={<IoT employee={employee} company={currentCompany}/>}/>
                    <Route path="/literatures" element={<Literatures employee={employee} company={currentCompany}/>}/>
                </Route>
            ) : <Route path="*" element={<Navigate to="/login" replace/>}/>}
        </Routes>
    </BrowserRouter>);
}

export default App;