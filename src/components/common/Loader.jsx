import React from 'react';
import { Button } from './Button';
import './Loader.css';

export const Loader = ({ message = "Loading Event Vault..." }) => {
  return (
    <div className="ev-loader-container">
      <div className="ev-spinner"></div>
      <p className="ev-loader-text">{message}</p>
    </div>
  );
};

export const ErrorState = ({ title = "Unable to process request", message = "An issue occurred while connecting to Event Vault services.", onRetry }) => {
  return (
    <div className="ev-error-container">
      <div className="ev-error-icon">!</div>
      <h3 className="ev-error-title">{title}</h3>
      <p className="ev-error-message">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Retry Connection
        </Button>
      )}
    </div>
  );
};
