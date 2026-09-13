import React from 'react';
import { Link } from 'react-router-dom';
import { AlertOctagon, Home } from 'lucide-react';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import './NotFound.css';

export const NotFound = () => {
  return (
    <PageContainer>
      <div className="ev-notfound-container">
        <AlertOctagon size={64} className="ev-notfound-icon" />
        <h1>404 - Route Not Found</h1>
        <p>The system route or ticket resource you requested could not be located in Event Vault.</p>

        <Link to="/">
          <Button variant="primary">
            <Home size={18} />
            <span>Return to Event Vault Home</span>
          </Button>
        </Link>
      </div>
    </PageContainer>
  );
};
