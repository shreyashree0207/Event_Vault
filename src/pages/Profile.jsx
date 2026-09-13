import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Mail, Calendar, ShieldCheck, Ticket, LogOut } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import { authService } from '../services/authService';
import { bookingService } from '../services/bookingService';
import './Profile.css';

export const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    if (!currentUser) {
      navigate('/login');
      return;
    }
    setUser(currentUser);

    bookingService.getUserBookings().then(setBookings).catch(console.error);
  }, [navigate]);

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <PageContainer>
      <div className="ev-profile-page">
        <div className="ev-profile-header-card">
          <img src={user.avatar} alt={user.name} className="ev-user-avatar" />
          <div className="ev-profile-user-info">
            <h2>{user.name}</h2>
            <div className="ev-profile-email">
              <Mail size={14} />
              <span>{user.email}</span>
            </div>
            <span className="ev-user-account-id">Account ID: {user.id}</span>
          </div>

          <Button variant="danger" size="sm" onClick={handleLogout} className="ev-profile-logout-btn">
            <LogOut size={16} />
            <span>Logout</span>
          </Button>
        </div>

        <div className="ev-profile-sections-grid">
          <div className="ev-profile-card">
            <div className="ev-pcard-header">
              <Ticket size={18} />
              <h3>My Bookings ({bookings.length})</h3>
            </div>
            {bookings.length === 0 ? (
              <p className="ev-empty-p-text">No active bookings.</p>
            ) : (
              <div className="ev-booking-history-list">
                {bookings.map(bk => (
                  <div key={bk.id} className="ev-history-item">
                    <div>
                      <strong>{bk.eventName}</strong>
                      <span className="ev-hist-sub">{bk.eventDate} • Seats: {bk.seats.join(', ')}</span>
                    </div>
                    <Link to={`/booking-confirmation/${bk.id}`}>
                      <span className="ev-view-receipt-link">View Receipt</span>
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="ev-profile-card">
            <div className="ev-pcard-header">
              <ShieldCheck size={18} />
              <h3>Account Security Settings</h3>
            </div>
            <div className="ev-security-options">
              <div className="ev-sec-item">
                <span>Multi-Factor Authentication (MFA)</span>
                <span className="ev-status-enabled">ENABLED</span>
              </div>
              <div className="ev-sec-item">
                <span>FastAPI JWT Authentication Token</span>
                <span className="ev-status-enabled">ACTIVE</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
