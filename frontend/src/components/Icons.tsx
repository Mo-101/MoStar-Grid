import React from 'react';

export interface IconProps {
  className?: string;
}

export const IfaIcon: React.FC<IconProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
    <path d="M12 2v20M2 12h20" stroke="currentColor" strokeWidth="2"/>
    <circle cx="12" cy="12" r="3" fill="currentColor"/>
    <path d="M12 9l3-3M12 9l-3-3M12 15l3 3M12 15l-3 3M9 12l-3 3M15 12l3 3M9 12l-3-3M15 12l3-3" stroke="currentColor" strokeWidth="1"/>
  </svg>
);

export const UbuntuIcon: React.FC<IconProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
    <circle cx="12" cy="12" r="4" fill="currentColor"/>
    <circle cx="12" cy="6" r="2" fill="currentColor"/>
    <circle cx="18" cy="12" r="2" fill="currentColor"/>
    <circle cx="12" cy="18" r="2" fill="currentColor"/>
    <circle cx="6" cy="12" r="2" fill="currentColor"/>
    <path d="M12 8v8M8 12h8" stroke="white" strokeWidth="1"/>
  </svg>
);

export const MoStarIcon: React.FC<IconProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" 
          fill="currentColor" stroke="currentColor" strokeWidth="1"/>
    <circle cx="12" cy="12" r="2" fill="white"/>
    <path d="M12 2v20M2 12h20" stroke="currentColor" strokeWidth="0.5" opacity="0.5"/>
  </svg>
);
