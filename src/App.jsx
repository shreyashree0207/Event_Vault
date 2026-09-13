import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Home } from './pages/Home';
import { Events } from './pages/Events';
import { EventDetails } from './pages/EventDetails';
import { WaitingRoom } from './pages/WaitingRoom';
import { Booking } from './pages/Booking';
import { BookingConfirmation } from './pages/BookingConfirmation';
import { MyTickets } from './pages/MyTickets';
import { Profile } from './pages/Profile';
import { Login, Register } from './pages/Login';
import { NotFound } from './pages/NotFound';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/events" element={<Events />} />
        <Route path="/events/:eventId" element={<EventDetails />} />
        <Route path="/waiting-room/:eventId" element={<WaitingRoom />} />
        <Route path="/booking/:eventId" element={<Booking />} />
        <Route path="/booking-confirmation/:bookingId" element={<BookingConfirmation />} />
        <Route path="/my-tickets" element={<MyTickets />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}
