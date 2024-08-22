import React, {useEffect, useState} from "react";
import Select from "react-select";
import {loadEstablishments} from "./Bookings";
import {API} from "../App";
import Room from "../models/Room";
import download from "downloadjs"
import {DefaultStorage} from "./CompaniesAndEstablishments";
import "../styles/IoT.css"

export default function IoT({employee, company}) {
    const [availableEstablishments, setAvailableEstablishments] = useState([]);
    const [establishment, setEstablishment] = useState(null);
    const [gateData, setGateData] = useState(/** @type {{room_id: int, code: string}}*/{});
    const [availableRooms, setAvailableRooms] = useState([]);
    const [room, setRoom] = useState(null);
    const [registeredIoTs, setRegisteredIoTs] = useState(/** @type {LightDevice[]} */[]);
    const [IoTsChanges, setIoTsChanges] = useState(/** @type {{ [id: string]: {light_type_name: DefaultStorage, details: DefaultStorage} }} */
        {});
    const [lightTypes, setLightTypes] = useState(/** @type {{ name: string }[]} */[]);
    const loadRooms = async () => {
        if (!establishment) return;
        await API.get(`/rooms/forEstablishment/${establishment.id}?I=room`)
                 .then((response) => {
                     setAvailableRooms(
                         response.data.map(room => new Room(room)).sort((a, b) => !a.label.localeCompare(b.label)));
                 }).catch((error) => {
                console.log(error.response);
            });
    }

    const loadIoTs = async () => {
        if (!room) setRegisteredIoTs([]); else {
            await API.get(`/light_devices/forRoom/${room.id}?I=light_device`)
                     .then((response) => {
                         setRegisteredIoTs(response.data);
                         setIoTsChanges(Object.fromEntries(response.data.map(device => [
                             device.id, {
                                 light_type_name: new DefaultStorage(device.light_type_name),
                                 details: new DefaultStorage(device.details ?? "")
                             }
                         ])))
                     })
                     .catch((error) => {
                         window.alert(error.response?.data ?? error)
                     })
        }

    }

    const loadLightTypes = async () => {
        await API.get('/light_types/?I=light_type')
                 .then((response) => {
                     setLightTypes(response.data.map(light_type => (
                         {name: light_type.name}
                     )));
                 })
                 .catch(error => {
                     window.alert(error.response?.data ?? error)
                 })
    }


    useEffect(() => {
        setEstablishment(null)
        loadEstablishments(company, setAvailableEstablishments);
    }, [company]);

    const loadGateData = async () => {
        if (!establishment) return;
        await API.get(`/light_devices/iot_registration_service/${establishment.id}`)
                 .then((response) => {
                     setGateData(response.data);
                 })
                 .catch((error) => {
                     /** @type {string} */
                     const error_response = error.response.data
                     if (error_response.includes("ERROR_TYPE: NO_GATE")) setGateData(null); else throw error
                 })
    }

    useEffect(() => {
        if (!establishment) {
            setRegisteredIoTs([])
            setIoTsChanges({})
            setGateData(null)
            setRoom(null)
        } else {
            loadGateData()
            loadRooms()
        }

    }, [establishment]);

    useEffect(() => {
        setRoom(availableRooms.find(room => room.id === gateData?.room_id))
    }, [gateData, availableRooms]);

    useEffect(() => {
        loadIoTs()
        loadLightTypes()
    }, [room])

    const handleGateOpening = async () => {
        await API.post(`/light_devices/iot_registration_service/${establishment.id}`)
                 .then(async (response) => {
                     await API.post(`/light_devices/iot_registration_service/${establishment.id}/room/${room.id}`)
                              .then(() => {
                                  loadGateData()
                              })
                 })
    }

    const handleGateClosing = async () => {
        await API.delete(`/light_devices/iot_registration_service/${establishment.id}`)
                 .then(response => {
                     loadGateData()
                 })
    }

    const handleGateRoomChanging = async () => {
        await API.post(`/light_devices/iot_registration_service/${establishment.id}/room/${room.id}`)
                 .then(() => {
                     loadGateData()
                 })
    }

    const handleDownloadGate = async () => {
        await API.get(`/light_devices/iot_registration_service/${establishment.id}/iot_file`, {
            responseType: "blob"
        })
                 .then(response => {
                     const file_name = response.headers['content-disposition'].match(/filename=(.*)/)[1]
                     download(response.data, file_name)
                 })
    }

    const handleDeviceChangesSave = async (device_id) => {
        await API.put(`/light_devices/${device_id}`, Object.fromEntries(
            Object.entries(IoTsChanges[device_id]).map(([key, defaultValue]) => [key, defaultValue.value])))
                 .then(response => {
                     loadIoTs()
                     window.alert(response.data.success_message)
                 })
                 .catch(error => {
                     window.alert(error.response?.data ?? error)
                 })
    }

    const handleDeviceDelete = async (device_id) => {
        await API.delete(`/light_devices/${device_id}`)
                 .then(response => {
                     loadIoTs()
                     window.alert(response.data.success_message)
                 })
                 .catch(error => {
                     window.alert(error.response?.data ?? error)
                 })
    }

    return (
        <div className="iot main-container">
            <div className="iot gate-pre-management">
                <h3>Manage registration code</h3>
                <Select className="iot establishment-selector"
                        options={availableEstablishments.map(establishment => (
                            {
                                label: establishment.address, value: establishment
                            }
                        ))}
                        onChange={({value}) => {
                            setEstablishment(value);
                        }}
                        value={establishment ? {label: establishment.address, value: establishment} : null}
                        placeholder="<Select an establishment>"/>
                {!establishment ? null : <div className="iot gate-management">
                    <h3>{!gateData ? 'Open gate' : `Manage gate`}</h3>
                    <Select
                        className="iot room-selector"
                        options={availableRooms.map(room => (
                            {label: room.label, value: room}
                        ))}
                        onChange={({value}) => {
                            setRoom(value);
                        }}
                        value={room ? {label: room.label, value: room} : null}
                        placeholder="<Select a room>"/>
                    <div className="iot gate-management gate-actions">
                        {!room ? null : (
                            !gateData ? <button onClick={handleGateOpening} className="iot open-gate">OPEN</button> : <>
                                <button onClick={handleGateRoomChanging} className="iot change-room">SAVE</button>
                                <button onClick={handleGateClosing} className="iot close-gate">CLOSE</button>
                            </>
                        )}
                    </div>
                    <div className="iot gate-management gate-as-file">
                        {!gateData || !room ? null :
                            <button onClick={handleDownloadGate} className="iot download-button">DOWNLOAD FILE</button>}
                    </div>
                </div>}
                <div className="iot registered-devices-management">
                    <h3>Registered IoT devices</h3>
                    <table>
                        <thead>
                        <tr>
                            <td>Device ID</td>
                            <td>PORT</td>
                            <td>Type</td>
                            <td>Details</td>
                            <td>Actions</td>
                        </tr>
                        </thead>
                        <tbody>
                        {registeredIoTs.map(device => <tr
                        className={`iot device-row ${
                            IoTsChanges[device.id]?.light_type_name.value ? 'CONFIGURED' : 'NON-CONFIGURED'
                        }`}>
                            <td>{device.id}</td>
                            <td>{device.port}</td>
                            <td>
                                {Object.keys(IoTsChanges).length === 0 ? null : <Select
                                    className="iot light-type-selector"
                                    options={lightTypes.map(lightType => (
                                        {label: lightType.name, value: lightType.name}
                                    ))}
                                    onChange={({value}) => {
                                        IoTsChanges[device.id].light_type_name.value = value
                                        setIoTsChanges({...IoTsChanges})
                                    }}
                                    value={IoTsChanges[device.id].light_type_name.value ? {
                                        label: IoTsChanges[device.id].light_type_name.value,
                                        value: IoTsChanges[device.id].light_type_name.value
                                    } : null}
                                    placeholder="<Select a light type>"
                                />}
                            </td>
                            <td>
                                    <textarea
                                        className="iot device-details"
                                        onChange={({target}) => {
                                            IoTsChanges[device.id].details.value = target.value
                                            setIoTsChanges({...IoTsChanges})
                                        }}>
                                        {device.details}
                                    </textarea>
                            </td>
                            <td>
                                {IoTsChanges[device.id]?.light_type_name.hasChanged
                                 || IoTsChanges[device.id]?.details.hasChanged ?
                                    <button onClick={() => handleDeviceChangesSave(device.id)}
                                            className="iot save-button">SAVE</button> : null}
                                <button onClick={() => handleDeviceDelete(device.id)}
                                        className="iot delete-button">DELETE
                                </button>
                            </td>
                        </tr>)}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    )
}