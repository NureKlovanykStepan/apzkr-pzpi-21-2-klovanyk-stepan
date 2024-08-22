import React from "react";
import '../styles/NavHeader.css'
import Select from "react-select";
import {Outlet, useNavigate} from "react-router-dom";
import DatePicker from "react-datepicker";

function NavHeader({employee, onLogout, companyManager}) {
    const navigate = useNavigate();
    const onValueChange = ({value}) => {
        companyManager.changeCompany(value);
    }

    const onBookingsClick = () => {
        navigate('/bookings');
    }

    const onEmployeesClick = () => {
        navigate('/employees');
    }

    const onCompAndEstabClick = () => {
        navigate('/companies_establishments');
    }

    const onIoTClick = () => {
        navigate('/iot_management');
    }

    const onLiteraturesClick = () => {
        navigate('/literatures');
    }
    return (
        <>
            <header className="header">
                <link rel="stylesheet"
                      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"/>
                <div className='header-container'>
                    <div className="header-elements-container header-role-options">
                        {employee.booking_manager ?
                            <button onClick={onBookingsClick} className="role-page-button">BOOKINGS</button> : null}
                        {employee.literature_manager ?
                            <button onClick={onLiteraturesClick} className="role-page-button">LITERATURES</button> :
                            null}
                        {employee.iot_manager ?
                            <button onClick={onIoTClick} className="role-page-button">IoTs</button> : null}
                        {employee.head_manager ?
                            <button onClick={onEmployeesClick} className="role-page-button">EMPLOYEES</button> : null}
                        {employee.head_manager && employee.establishment.company.global_access_company ?
                            <button onClick={onCompAndEstabClick} className="role-page-button"
                                    id="global-manager">COMPANIES & ESTABLISHMENTS</button> : null}
                    </div>
                    <div className='header-elements-container header-employee-infoblock'>
                        <p className="header-employee-email header-p"><i
                            className="fa fa-user header-employee-icon"></i>{employee.user.email}</p>
                        <div className="header-employee-company-container">
                            <p className="header-employee-company-text header-p">Company: </p>
                            {companyManager && companyManager.selectedCompany ? (
                                companyManager.availableCompanies.length > 1 ?
                                    <Select className="header-employee-select" options={companyManager.asOptions}
                                            value={{
                                                value: companyManager.selectedCompany.id,
                                                label: companyManager.selectedCompany.name
                                            }} onChange={onValueChange}/> : <p>{companyManager.selectedCompany.name}</p>
                            ) : null}
                        </div>
                        <button className="header-employee-logout-button" onClick={onLogout}>Log out<i
                            className="fa fa-sign-out header-logout-icon"></i></button>
                    </div>
                </div>
            </header>
            <Outlet/>
        </>
    );
}

export default NavHeader