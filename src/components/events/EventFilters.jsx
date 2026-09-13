import React from 'react';
import { Search, Filter } from 'lucide-react';
import './EventFilters.css';

export const EventFilters = ({
  search,
  setSearch,
  category,
  setCategory,
  location,
  setLocation,
  categories
}) => {
  return (
    <div className="ev-filters-bar">
      <div className="ev-filter-search">
        <Search size={18} className="ev-search-icon" />
        <input
          type="text"
          placeholder="Search by title, artist, venue..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="ev-search-input"
        />
      </div>

      <div className="ev-filter-group">
        <div className="ev-select-wrapper">
          <Filter size={16} className="ev-select-icon" />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="ev-filter-select"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <input
          type="text"
          placeholder="Location (e.g. Los Angeles)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="ev-filter-input"
        />
      </div>
    </div>
  );
};
