import React, {useEffect} from "react";
import {API} from "../App";
import Company from "../models/Company";
import PropTypes from "prop-types";
import Country from "../models/Country";
import Select from "react-select";
import "../styles/CompaniesAndEstablishments.css"


export class DefaultStorage {
    constructor(defaultValue) {
        //this.company = company;
        this.defaultValue = defaultValue;
        this._value = defaultValue
    }

    get value() {
        return this._value
    }

    set value(value) {
        this._value = value
    }

    get hasChanged() {
        return this.value !== this.defaultValue
    }


}

export default function CompaniesAndEstablishments({employee, company, loadEmployee})
{
    const [availableCompanies, setAvailableCompanies] = React.useState(/** @type Company[] */
        []);
    const [companyChanges, setCompanyChanges] = React.useState(/** @type {{ [key: string]: {name: DefaultStorage, global_access_company: DefaultStorage} }} */
        {});
    const [establishmentChanges, setEstablishmentChanges] = React.useState(/** @type {{ [country_id: string]: {[establishment_id: string] : {address: DefaultStorage, country_id: DefaultStorage}} }} */
        {})
    const [availableCountries, setAvailableCountries] = React.useState(/** @type Country[] */
        []);

    const [companyCreationData, setCompanyCreationData] = React.useState({name: "", global_access_company: false});
    const [establishmentCreationData, setEstablishmentCreationData] = React.useState({
        address: "",
        country_id: null,
        company_id: null
    });

    const loadCompanies = async () =>
    {
        await API.get('/companies/?I=company,establishment')
            .then((response) =>
            {
                setAvailableCompanies(response.data.map(company => new Company(company)));

            })
            .catch(error =>
            {
                window.alert(error.response?.data ?? error)
            })

    }

    const loadCountries = async () =>
    {
        await API.get('/countries?I=country')
            .then((response) =>
            {
                setAvailableCountries(response.data.map(country => new Country(country)));
            })
            .catch(error =>
            {
                window.alert(error.response?.data ?? error)
            })
    }

    useEffect(
        () =>
        {
            loadCompanies();
            loadCountries();
        },
        []
    )

    useEffect(
        () =>
        {
            const companiesMutableData = availableCompanies.map(company => [
                company.id, {
                    name: new DefaultStorage(company.name),
                    global_access_company: new DefaultStorage(company.global_access_company),
                }
            ])
            setCompanyChanges(Object.fromEntries(companiesMutableData))
            const establishmentsMutableData = availableCompanies.map(company => [
                company.id, Object.fromEntries(company.establishments.map(establishment => [
                    establishment.id, {
                        address: new DefaultStorage(establishment.address),
                        country_id: new DefaultStorage(establishment.country_id),
                    }
                ]))
            ])
            setEstablishmentChanges(Object.fromEntries(establishmentsMutableData))
        },
        [availableCompanies]
    );


    const handleCompanySave = async (company_id) =>
    {
        const data = Object.fromEntries(Object.entries(companyChanges[company_id])
            .map(([key, value]) => [key, value.value]))
        await API.put(
            `/companies/${company_id}`,
            data
        )
            .then(response =>
            {
                window.alert(response.data.success_message)
                loadCompanies()
                loadEmployee()
            })
            .catch(error =>
            {
                window.alert(error.response?.data ?? error)
            })
    }

    const handleCompanyDelete = async (company_id) =>
    {
        await API.delete(`/companies/${company_id}`)
            .then(response =>
            {
                window.alert(response.data.success_message)
                loadCompanies()
                loadEmployee()
            })
            .catch(error =>
            {
                window.alert(error.response?.data ?? error)
            })
    }

    const handleEstablishmentSave = async (
        company_id,
        establishment_id
    ) =>
    {
        const data = Object.fromEntries(Object.entries(establishmentChanges[company_id][establishment_id])
            .map(([key, value]) => [key, value.value]))
        await API.put(
            `/establishments/${establishment_id}`,
            data
        )
            .then(response =>
            {
                window.alert(response.data.success_message)
                loadCompanies()
                loadEmployee()
            })
            .catch(error =>
            {
                window.alert(error.response?.data ?? error)
            })
    }

    const handleEstablishmentDelete = async (establishment_id) =>
    {
        await API.delete(`/establishments/${establishment_id}`)
            .then(response =>
            {
                window.alert(response.data.success_message)
                loadCompanies()
                loadEmployee()
            })
            .catch(error =>
            {
                window.alert(error.response?.data ?? error)
            })
    }

    const handleCompanyCreation = async () =>
    {
        await API.post(
            '/companies/',
            companyCreationData
        )
            .then(response =>
            {
                window.alert(response.data.success_message)
                loadCompanies()
                loadEmployee()
            })
            .catch(error =>
            {
                window.alert(error.response?.data ?? error)
            })
    }

    const handleEstablishmentCreation = async () =>
    {
        await API.post(
            `/establishments/`,
            establishmentCreationData
        )
            .then(response =>
            {
                window.alert(response.data.success_message)
                loadCompanies()
                loadEmployee()
            })
            .catch(error =>
            {
                window.alert(error.response?.data ?? error)
            })
    }

    return (
        <div className="cne container">
            <h1>Companies & Establishments Management</h1>
            <div className="cne container-data">
                <table className="cne table companies-table">
                    <thead>
                    <tr className="cne table-header">
                        <th>Name</th>
                        <th>Global Access</th>
                        <th>Actions</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr className="cne table-row company-row create-company-row">
                        <td className="cne table-cell company-name">
                            <input onInput={e =>
                            {
                                companyCreationData.name = e.currentTarget.value
                                setCompanyCreationData({...companyCreationData})
                            }}
                                   type="text"
                            />
                        </td>
                        <td className="cne table-cell global-access">
                            <input onChange={e =>
                            {
                                companyCreationData.global_access_company = e.currentTarget.checked
                                setCompanyCreationData({...companyCreationData})
                            }}
                                   type="checkbox"
                            />
                        </td>
                        <td className="cne table-cell actions">
                            <div className="cne company-actions actions-container">
                                {companyCreationData.name.length < 3 ? null :
                                    <button className="cne save-button company-action"
                                            onClick={() => handleCompanyCreation()}
                                    >Create
                                    </button>}
                            </div>
                        </td>
                    </tr>
                    {Object.entries(companyChanges)
                        .map(([company_id, {name, global_access_company}]) => (
                            <>
                                <tr className="cne table-row company-row">
                                    <td className="cne table-cell company-name"><input onInput={e =>
                                    {
                                        name.value = e.currentTarget.value
                                        setCompanyChanges({...companyChanges})
                                    }}
                                                                                       defaultValue={name.value}
                                                                                       type="text"
                                    /></td>
                                    <td className="cne table-cell global-access"><input onChange={e =>
                                    {
                                        global_access_company.value = e.currentTarget.checked
                                        setCompanyChanges({...companyChanges})
                                    }}
                                                                                        checked={global_access_company.value}
                                                                                        type="checkbox"
                                    /></td>
                                    <td className="cne table-cell actions">
                                        <div className="cne company-actions actions-container">
                                            {(
                                                 name.hasChanged || global_access_company.hasChanged
                                             ) && name.value.length >= 3 ?
                                                <button className="cne save-button company-action"
                                                        onClick={() => handleCompanySave(company_id)}
                                                >Save</button> : null}
                                            <button className="cne delete-button company-action"
                                                    onClick={() => handleCompanyDelete(company_id)}
                                            >Delete
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                <tr className="cne table-row establishment-row">
                                    <td colSpan="0">
                                        <table className="cne table establishment-table">
                                            <thead>
                                            <tr className="cne table-header">
                                                <th>Address</th>
                                                <th>Country</th>
                                                <th>Actions</th>
                                            </tr>
                                            </thead>
                                            <tbody>
                                            <tr className="cne table-row establishment-row create-establishment-row">
                                                <td className="cne table-cell establishment-address">
                                                    <input onInput={e =>
                                                    {
                                                        establishmentCreationData.address = e.currentTarget.value
                                                        setEstablishmentCreationData({
                                                            ...establishmentCreationData,
                                                            company_id: company_id
                                                        })
                                                    }}
                                                           type="text"
                                                    />
                                                </td>
                                                <td className="cne table-cell establishment-country">
                                                    {availableCountries.length === 0 ? null : <Select
                                                        className="cne establishment-country-select select"
                                                        onChange={e =>
                                                        {
                                                            establishmentCreationData.country_id = Number.parseInt(e.value)
                                                            setEstablishmentCreationData({
                                                                ...establishmentCreationData,
                                                                company_id: company_id
                                                            })
                                                        }}
                                                        options={availableCountries.map(country => new Option(
                                                            `[${country.charcode}] ${country.name}`,
                                                            country.id
                                                        ))}
                                                        placeholder="<select country>"
                                                    />}

                                                </td>
                                                <td className="cne table-cell actions">
                                                    <div className="cne establishment-actions actions-container">
                                                        {establishmentCreationData.country_id === null
                                                         || establishmentCreationData.address.length < 3
                                                         || establishmentCreationData.company_id !== company_id ? null :
                                                            <button className="cne save-button establishment-action"
                                                                    onClick={() => handleEstablishmentCreation()}
                                                            >Create
                                                            </button>}
                                                    </div>
                                                </td>
                                            </tr>

                                            {Object.entries(establishmentChanges[company_id])
                                                .map(([establishment_id, {address, country_id}]) => (
                                                    <tr className="cne table-row establishment-row">
                                                        <td className="cne table-cell establishment-address">
                                                            <input onInput={e =>
                                                            {
                                                                address.value = e.currentTarget.value
                                                                setEstablishmentChanges({...establishmentChanges})
                                                            }}
                                                                   defaultValue={address.value}
                                                                   type="text"
                                                            />
                                                        </td>
                                                        <td className="cne table-cell establishment-country">
                                                            {availableCountries.length === 0 ? null : <Select
                                                                className="cne establishment-country-select select"
                                                                onChange={e =>
                                                                {
                                                                    country_id.value = Number.parseInt(e.value)
                                                                    setEstablishmentChanges({...establishmentChanges})
                                                                }}
                                                                value={[
                                                                    availableCountries.find(country => country.id
                                                                                                       === country_id.value)
                                                                ].filter(Boolean)
                                                                    .map(country => new Option(
                                                                        `[${country.charcode}] ${country.name}`,
                                                                        country.id
                                                                    ))}
                                                                options={availableCountries.map(country => new Option(
                                                                    `[${country.charcode}] ${country.name}`,
                                                                    country.id
                                                                ))}
                                                                placeholder="<select country>"
                                                            />}
                                                        </td>
                                                        <td className="cne table-cell actions">
                                                            <div className="cne establishment-actions actions-container">
                                                                {(
                                                                     address.hasChanged || country_id.hasChanged
                                                                 ) && address.value.length >= 3 ? <button
                                                                    className="cne save-button establishment-action"
                                                                    onClick={() => handleEstablishmentSave(
                                                                        company_id,
                                                                        establishment_id
                                                                    )}
                                                                >Save
                                                                </button> : null}
                                                                <button
                                                                    className="cne delete-button establishment-action"
                                                                    onClick={() => handleEstablishmentDelete(establishment_id)}
                                                                >Delete
                                                                </button>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

