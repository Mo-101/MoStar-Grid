import React from 'react';

export interface MoStarLogoProps {
  className?: string;
}

export const MoStarLogo: React.FC<MoStarLogoProps> = ({ className = '' }) => (
  <svg
    className={className}
    viewBox="0 0 200 60"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    {/* MoStar Text */}
    <text x="10" y="40" fontFamily="Arial, sans-serif" fontSize="32" fontWeight="bold" fill="white">
      MoStar
    </text>
    
    {/* Star Icon */}
    <path
      d="M160 15l6.18 12.52L180 30.81l-10 9.74 2.36 13.76L160 48.54l-12.36 5.77L150 40.55l-10-9.74 13.82-3.29L160 15z"
      fill="#fbbf24"
      stroke="#f59e0b"
      strokeWidth="1"
    />
    
    {/* Grid Lines */}
    <path d="M140 10v40M180 10v40M140 20h40M140 30h40M140 40h40" 
          stroke="#60a5fa" strokeWidth="0.5" opacity="0.6"/>
    
    {/* Small dots representing grid nodes */}
    <circle cx="145" cy="15" r="1" fill="#60a5fa"/>
    <circle cx="155" cy="15" r="1" fill="#60a5fa"/>
    <circle cx="165" cy="15" r="1" fill="#60a5fa"/>
    <circle cx="175" cy="15" r="1" fill="#60a5fa"/>
    <circle cx="145" cy="25" r="1" fill="#60a5fa"/>
    <circle cx="155" cy="25" r="1" fill="#60a5fa"/>
    <circle cx="175" cy="25" r="1" fill="#60a5fa"/>
    <circle cx="145" cy="35" r="1" fill="#60a5fa"/>
    <circle cx="155" cy="35" r="1" fill="#60a5fa"/>
    <circle cx="175" cy="35" r="1" fill="#60a5fa"/>
    <circle cx="145" cy="45" r="1" fill="#60a5fa"/>
    <circle cx="155" cy="45" r="1" fill="#60a5fa"/>
    <circle cx="165" cy="45" r="1" fill="#60a5fa"/>
    <circle cx="175" cy="45" r="1" fill="#60a5fa"/>
  </svg>
);
