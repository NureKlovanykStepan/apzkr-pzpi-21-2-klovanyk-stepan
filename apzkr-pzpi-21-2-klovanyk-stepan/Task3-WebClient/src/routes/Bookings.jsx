import React, {useEffect, useState} from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "../styles/Bookings.css";
import Select from "react-select";
import {API} from "../App";
import Establishment from "../models/Establishment";
import Room from "../models/Room";
import Booking from "../models/Booking";
import User from "../models/User";
import moment from "moment";

export async function loadEstablishments(company, setAvailableEstablishments) {
    if (!company) return;
    await API.get(`/establishments/forCompany/${company.id}?I=establishment`)
        .then((response) => {
            setAvailableEstablishments(response.data.map(establishment => new Establishment(establishment)).sort((a, b) => !a.address.localeCompare(b.address)));
        }).catch((error) => {
            console.log(error.response);
        });
}
export default function Bookings({employee, company}) {
    const [availableEstablishments, setAvailableEstablishments] = useState([]);
    const [establishment, setEstablishment] = useState(null);
    const [availableRooms, setAvailableRooms] = useState([]);
    const [room, setRoom] = useState(null);
    const [bookings, setBookings] = useState([]);
    const [users, setUsers] = useState([]);
    const [userEmail, setUserEmail] = useState(null);
    const [isDateTimeSelectorOpened, setIsDateTimeSelectorOpened] = useState(false);

    const [registrationDate, setRegistrationDate] = useState(new Date());
    const [expirationDate, setExpirationDate] = useState(new Date());
    const minutesRange = 15;
    const minutesGap = 60;
    const minutesMinBooking = 120;




    const loadRooms = async () => {
        if (!establishment) return;
        await API.get(`/rooms/forEstablishment/${establishment.id}?I=room`)
            .then((response) => {
                setAvailableRooms(response.data.map(room => new Room(room)).sort((a, b) => !a.label.localeCompare(b.label)));
            }).catch((error) => {
                console.log(error.response);
            });
    }

    const loadBookings = async () => {
        if (!room) return;
        await API.get(`/bookings/forRoom/${room.id}?I=booking,user.email`)
            .then((response) => {
                setBookings(response.data);
            }).catch((error) => {
                console.log(error.response);
            });
    }

    const onActionCancelBooking = async (booking) => {
        await API.delete(`/bookings/${booking.id}`)
            .then((response) => {
                loadBookings();
                console.log(bookings)
            }).catch((error) => {
                console.log(error.response);
            });
    }

    const checkDateAvailableDay = (date) => {
        if (date < new Date()) return false;

        for (let booking of bookings) {
            let reg = moment(booking.registration_time).subtract(minutesGap, 'minutes').toDate();
            let exp = moment(booking.expiration_time).add(minutesGap, 'minutes').toDate();
            if ((reg <= date && date <= exp)) {
                let oldDate = date;
                date = exp;
                if (oldDate.getDate() !== date.getDate() || oldDate.getMonth() !== date.getMonth() || oldDate.getFullYear() !== date.getFullYear()) return false
            }
        }
        return true;
    }

    const checkDateAvailableDaySpan = (date) => {
        if (date < new Date()) return false;

        for (let booking of bookings) {
            let reg = moment(booking.registration_time).subtract(minutesGap, 'minutes').toDate();
            if (registrationDate && date > registrationDate && registrationDate < reg) return false
            let exp = moment(booking.expiration_time).add(minutesGap, 'minutes').toDate();
            if ((reg <= date && date <= exp)) {
                let oldDate = date;
                date = exp;
                if (oldDate.getDate() !== date.getDate() || oldDate.getMonth() !== date.getMonth() || oldDate.getFullYear() !== date.getFullYear()) return false
            }
        }
        return true;
    }

    const checkDateAvailableHour = (date) => {
        if (date < new Date()) return false;

        for (let booking of bookings) {
            let reg = moment(booking.registration_time).subtract(minutesGap, 'minutes').toDate();
            let exp = moment(booking.expiration_time).add(minutesGap, 'minutes').toDate();
            if ((reg <= date && date <= exp)) {
                return false
            }
        }
        return true;
    }

    const filterDateStartPoint = (date) => {
        date = new Date(date)
        return checkDateAvailableDay(date)
    }

    const filterTimeStartPoint = (date) => {
        date = new Date(date)
        return checkDateAvailableHour(date)
    }

    const filterDateEndPoint = (date) => {
        date = new Date(date)
        return checkDateAvailableDaySpan(date) && date >= new Date(registrationDate).setHours(0, 0, 0, 0)
    }
    const filterTimeEndPoint = (date) => {
        date = new Date(date)
        return checkDateAvailableHour(date) && new Date(date.getTime() - registrationDate.getTime()) / 60000 >= minutesMinBooking
    }

    const onUserAdd = async (email) => {
        if (!email) return;
        if (users.find(user => user.email === email)) return;
        await API.get(`/users/${email}?I=user`)
            .then((response) => {
                setUsers([...users, new User(response.data)]);
            }).catch((error) => {
                window.alert(error.response.data)
            })
    }

    const onBookingCreation = async () => {
        let createdId = null
        await API.post(`/bookings/`, {
            room_id: room.id,
            registration_time: registrationDate.toISOString(),
            expiration_time: expirationDate.toISOString(),
            registrator_email: employee.user_email
        }).then((response) => {
            createdId = response.data.pk_data.id;
            setRegistrationDate(null)
            setExpirationDate(null)
        }).catch((error) => {
            window.alert(error.response.data)
        })
        console.log(createdId)
        await Promise.all(users.map(async (user) => {
            await API.post('/user_booking_x/', {
                user_email: user.email, booking_id: createdId
            })
        }))
        window.alert("Booking created");
        loadBookings();
        setUsers([])
    }

    useEffect(() => {
        setEstablishment(null)
        setAvailableEstablishments([])
        loadEstablishments(company, setAvailableEstablishments);
    }, [company]);

    useEffect(() => {
        setRoom(null)
        setAvailableRooms([])
        loadRooms();
    }, [establishment]);

    useEffect(() => {
        loadBookings();
        setBookings([])
        setExpirationDate(null)
        setRegistrationDate(null)
    }, [room]);

    return (<div className="bookings main-container">
        <div className="bookings selectors">
            <Select
                options={availableEstablishments.map(establishment => ({
                    label: establishment.address, value: establishment
                }))}
                onChange={({value}) => {
                    setEstablishment(value);
                }}
                value={establishment ? {label: establishment.address, value: establishment} : null}
                placeholder="<Select an establishment>"/>
            <Select
                options={availableRooms.map(room => ({label: room.label, value: room}))}
                onChange={({value}) => {
                    setRoom(value);
                }}
                value={room ? {label: room.label, value: room} : null}
                placeholder="<Select a room>"/>
        </div>
        {!room ? null : <div className="bookings create-booking">
            <DatePicker
                selected={registrationDate}
                onChange={(date) => {
                    setExpirationDate(null)
                    setRegistrationDate(date);
                }}
                showTimeSelect={true}
                timeIntervals={minutesRange}
                timeFormat="HH:mm"
                filterDate={filterDateStartPoint}
                filterTime={filterTimeStartPoint}
                id={bookings.length.toString()}
                dateFormat="dd-MM-yyyy HH:mm" onChangeRaw={(event) => {
                event.preventDefault();
            }} onCalendarClose={() => {
                setIsDateTimeSelectorOpened(false)
                if (!filterDateStartPoint(registrationDate) || !filterTimeStartPoint(registrationDate)) setRegistrationDate(null)
            }} onCalendarOpen={() => setIsDateTimeSelectorOpened(true)}
            />
            {!registrationDate ? null : <DatePicker
                selected={expirationDate}
                onChange={(date) => {
                    setExpirationDate(date);
                }}
                showTimeSelect={true}
                timeIntervals={minutesRange}
                timeFormat="HH:mm"
                filterDate={filterDateEndPoint}
                filterTime={filterTimeEndPoint}
                id={bookings.length.toString()}
                dateFormat="dd-MM-yyyy HH:mm" onCalendarClose={() => {
                setIsDateTimeSelectorOpened(false)
                if (!filterDateStartPoint(expirationDate) || !filterTimeEndPoint(expirationDate)) setExpirationDate(null)
            }} onCalendarOpen={() => setIsDateTimeSelectorOpened(true)}/>}
            <ul className="bookings booking-users">
                {users.map(user => <li key={user.email}>{user.email}
                    <button className="bookings booking-users cancel-user-addition"
                            onClick={() => setUsers(users.filter(u => u.email !== user.email))}>Cancel
                    </button>
                </li>)}
                <li>
                    <div className="bookings booking-users add-form">
                        <input onChange={e => setUserEmail(e.target.value)} type="email"/>
                        <button onClick={() => {
                            onUserAdd(userEmail)
                        }}>Add
                        </button>
                    </div>
                </li>
            </ul>
            {!isDateTimeSelectorOpened && registrationDate && expirationDate && users.length > 0 ?
                <button className="bookings create-booking confirm-booking-creation"
                        onClick={onBookingCreation}>BOOK</button> : null}
        </div>}
        <div className="bookings table-existing">
            <table>
                <thead>
                <tr>
                    <th>id</th>
                    <th>registration time</th>
                    <th>expiration time</th>
                    <th>registrator</th>
                    <th>users</th>
                    <th>actions</th>
                </tr>
                </thead>
                <tbody>
                {bookings.map((data) => {
                    let booking = new Booking(data)
                    return <tr>
                        <td>{booking.id}</td>
                        <td>{new Date(booking.registration_time).toLocaleString()}</td>
                        <td>{new Date(booking.expiration_time).toLocaleString()}</td>
                        <td>{booking.registrator_email}</td>
                        <td>
                            <ul>
                                {booking.users.map(user => <li key={user.email}>{user.email}</li>)}
                            </ul>
                        </td>
                        <td>
                            <button onClick={() => {
                                onActionCancelBooking(booking)
                            }}>Cancel
                            </button>
                        </td>
                    </tr>


                })}
                </tbody>
            </table>
        </div>
    </div>);
}