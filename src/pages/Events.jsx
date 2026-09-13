import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { EventFilters } from '../components/events/EventFilters';
import { EventList } from '../components/events/EventList';
import { Loader, ErrorState } from '../components/common/Loader';
import { eventService } from '../services/eventService';

const CATEGORIES = ['Music', 'Technology', 'Sports', 'Theatre', 'Comedy', 'Cultural'];

export const Events = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [location, setLocation] = useState('');

  const fetchEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await eventService.getEvents({ search, category, location });
      setEvents(data);
    } catch (err) {
      setError(err.message || 'Unable to fetch events.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [search, category, location]);

  return (
    <PageContainer>
      <div className="ev-events-page-header">
        <h1 className="ev-page-title">Upcoming Live Events</h1>
        <p className="ev-page-subtitle">Discover high-demand concerts, conferences, and championship games.</p>
      </div>

      <EventFilters
        search={search}
        setSearch={setSearch}
        category={category}
        setCategory={setCategory}
        location={location}
        setLocation={setLocation}
        categories={CATEGORIES}
      />

      {loading ? (
        <Loader message="Querying Event Vault Index..." />
      ) : error ? (
        <ErrorState title="Unable to load events" message={error} onRetry={fetchEvents} />
      ) : (
        <EventList events={events} />
      )}
    </PageContainer>
  );
};
