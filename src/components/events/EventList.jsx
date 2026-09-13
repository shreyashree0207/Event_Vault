import React from 'react';
import { EventCard } from './EventCard';
import './EventList.css';

export const EventList = ({ events }) => {
  if (events.length === 0) {
    return (
      <div className="ev-empty-events">
        <h3>No events found</h3>
        <p>Try adjusting your search criteria or category filters.</p>
      </div>
    );
  }

  return (
    <div className="ev-event-grid">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
};
