'use client';

import React from 'react';

export interface ActiveToast {
  id: string;
  name: string;
  location: string;
  message: string;
  color: string;
}

interface AgenticToastContainerProps {
  toasts: ActiveToast[];
  onDismiss: (id: string) => void;
}

export const AgenticToastContainer: React.FC<AgenticToastContainerProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="absolute top-6 right-6 z-50 flex flex-col gap-3 w-96 pointer-events-auto font-mono text-[11px]">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="bg-slate-950/85 backdrop-blur-xl border border-slate-800/80 p-4 rounded-xl shadow-lg relative overflow-hidden group"
          style={{ borderLeft: `3px solid ${toast.color}` }}
        >
          {/* Ambient Glowing Background */}
          <div 
            className="absolute -right-10 -top-10 w-24 h-24 rounded-full blur-2xl opacity-15 pointer-events-none transition-all duration-500 group-hover:opacity-25"
            style={{ backgroundColor: toast.color }}
          />

          <div className="flex justify-between items-start mb-1 relative z-10">
            <div>
              <span className="font-bold text-white tracking-wide uppercase">{toast.name}</span>
              <span className="mx-1.5 text-slate-600">|</span>
              <span className="text-slate-400 text-[10px] uppercase">{toast.location}</span>
            </div>
            <button
              onClick={() => onDismiss(toast.id)}
              className="text-slate-500 hover:text-white transition-colors p-0.5"
            >
              ✕
            </button>
          </div>
          
          <p className="text-slate-300 leading-relaxed mt-1 relative z-10">{toast.message}</p>
          
          {/* Progress Tracer Line */}
          <div className="w-full bg-slate-900 h-0.5 mt-2.5 rounded-full overflow-hidden">
            <div 
              className="h-full animate-pulse" 
              style={{ 
                backgroundColor: toast.color,
                width: '100%',
                animationDuration: '3s'
              }} 
            />
          </div>
        </div>
      ))}
    </div>
  );
};
