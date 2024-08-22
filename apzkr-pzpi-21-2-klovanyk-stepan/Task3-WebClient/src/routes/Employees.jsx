import React, {useEffect, useState} from "react";
import {API} from "../App";
import Establishment from "../models/Establishment";
import Bookings, {loadEstablishments} from "./Bookings";
import Employee from "../models/Employee";
import Select from "react-select";
import "../styles/Employees.css"


export default function Employees({employee, company, loadEmployee}) {
    const [availableEstablishments, setAvailableEstablishments] = useState([]);
    const [establishment, setEstablishment] = useState(null);
    const [availableEmployees, setAvailableEmployees] = useState([]);

    const [newEmployeeData, setNewEmployeeData] = useState({
        user_email: "",
        establishment_id: "",
        iot_manager: false,
        head_manager: false,
        booking_manager: false,
        literature_manager: false
    })

    useEffect(
        () => {
            setEstablishment(null)
            loadEstablishments(
                company,
                setAvailableEstablishments
            );
        },
        [company]
    );

    const loadEmployees = async () => {
        if (!establishment) return;
        await API.get(`/employees?I=employee,user`)
            .then((response) => {
                setAvailableEmployees(
                    response.data.filter(employee => employee.establishment_id === establishment.id)
                        .map(
                            employee => new Employee(employee)));
            })
            .catch(async (error) => {
                await API.get(`/employees/my?I=employee,user`)
                .then((response) => {
                    setAvailableEmployees(
                        response.data.filter(employee => employee.establishment_id === establishment.id)
                            .map(
                                employee => new Employee(employee)));
                })
                .catch((error) => {
                    console.log(error.response);
                })
            })
    }
    useEffect(
        () => {
            setAvailableEmployees([])
            loadEmployees();
        },
        [establishment]
    );

    const onEmployeeUpdate = async (event) => {
        event.preventDefault();

        const data = new FormData(event.currentTarget);
        const user_email = data.get("user_email");
        const send_data = Object.fromEntries(Array.from(data.entries())
            .filter(entry => entry[0] !== "user_email")
            .map(entry => [entry[0], entry[1] !== "false"])
        )
        await API.put(
            `/employees/${user_email}`,
            send_data,
        )
            .then(response => {
                window.alert(`Employee "${user_email}" updated`);
                if (user_email === employee.user.email) loadEmployee()
            })
            .catch(error => {
                window.alert(JSON.stringify(error.response.data));
            })
    }

    const onEmployeeDelete = async (employee_to_delete) => {
        await API.delete(`/employees/${employee_to_delete.user.email}`)
            .then((response) => {
                loadEmployees();
            })
            .catch((error) => {
                console.log(error.response);
            })
    }

    const onEmployeeCreate = async () => {
        await API.post(
            `/employees/`,
            {
                ...newEmployeeData, establishment_id: establishment.id
            }
        )
            .then((response) => {
                window.alert("Employee created");
                loadEmployees();
            })
            .catch((error) => {
                window.alert(error.response.data);
            })
            .catch((non_response_error) => {
                console.log(non_response_error.response);
            })
    }

    return (
        <div className="employees container">
            <Select className="employees establishment-selector"
                    options={availableEstablishments.map(establishment => (
                        {
                            label: establishment.address, value: establishment
                        }
                    ))}
                    onChange={({value}) => {
                        setEstablishment(value);
                    }}
                    value={establishment
                        ? {label: establishment.address, value: establishment}
                        : null}
                    placeholder="<Select an establishment>"/>
            {!establishment
                ? null
                : <table className="employees table">
                    <thead>
                    <tr>
                        <th>Email</th>
                        <th>Roles</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td className="employees email">
                            <input
                                onChange={event => setNewEmployeeData({
                                    ...newEmployeeData, user_email: event.target.value
                                })}
                                type="email"
                                name="user_email"
                                placeholder="<user_email>"/>
                        </td>
                        <td className="employees roles">
                            <form className="employees roles-form">
                                {Object.keys(employee)
                                    .filter(key => key.endsWith("_manager"))
                                    .map(key =>
                                        <div className="employees role">
                                            <label>{key}<input name={key}
                                                               type="checkbox"
                                                               checked={newEmployeeData[key]}
                                                               onChange={
                                                                   ({target}) => {
                                                                       setNewEmployeeData(prev => (
                                                                           {...prev, [key]: target.checked}
                                                                       ))
                                                                   }
                                                               }/>
                                            </label>
                                        </div>
                                    )}
                            </form>
                            <div className="employees actions">
                                <button onClick={onEmployeeCreate}
                                        className="employees save-button"
                                        type="submit">Create
                                </button>
                            </div>
                        </td>
                    </tr>
                    {
                        availableEmployees.map(availableEmployee => (
                            <tr key={availableEmployee.user.email}>
                                <td className="employees email">{availableEmployee.user.email}</td>
                                <td className="employees roles">
                                    <form className="employees roles-form"
                                          onSubmit={onEmployeeUpdate}>
                                        {Object.keys(availableEmployee)
                                            .filter(key => key.endsWith("_manager"))
                                            .map(key =>
                                                <div className="employees role">
                                                    <label>{key}<input name={key}
                                                                       type="checkbox"
                                                                       checked={availableEmployee[key]}
                                                                       onChange={
                                                                           ({target}) => {
                                                                               availableEmployee[key] = target.checked
                                                                               setAvailableEmployees(prev => [...prev])
                                                                           }
                                                                       }/></label>
                                                    <input type="hidden"
                                                           name={key}
                                                           value={availableEmployee[key]}/>
                                                </div>
                                            )}
                                        <input type="hidden"
                                               name="user_email"
                                               value={availableEmployee.user.email}/>
                                        <div className="employees actions">
                                            <button className="employees save-button"
                                                    type="submit">Save
                                            </button>
                                            <button className="employees delete-button"
                                                    onClick={() => onEmployeeDelete(availableEmployee)}
                                                    type="button">Delete
                                            </button>
                                        </div>
                                    </form>
                                </td>
                            </tr>
                        ))
                    }

                    </tbody>
                </table>}

        </div>
    );
}