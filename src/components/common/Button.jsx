import React from 'react';
import './Button.css';

export const Button = ({
  children,
  variant = 'primary', // primary, secondary, outline, danger
  size = 'md', // sm, md, lg
  isLoading = false,
  icon: Icon,
  disabled,
  className = '',
  ...props
}) => {
  return (
    <button
      className={`ev-button ev-button--${variant} ev-button--${size} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="ev-button__loader"></span>
      ) : (
        <>
          {Icon && <Icon className="ev-button__icon" size={size === 'sm' ? 16 : 18} />}
          <span>{children}</span>
        </>
      )}
    </button>
  );
};
