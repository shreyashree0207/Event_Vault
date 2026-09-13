import React from 'react';
import { Navbar } from './Navbar';
import { Footer } from './Footer';
import './PageContainer.css';

export const PageContainer = ({ children, className = '' }) => {
  return (
    <div className="ev-app-shell">
      <Navbar />
      <main className={`ev-main-content ${className}`}>
        {children}
      </main>
      <Footer />
    </div>
  );
};
