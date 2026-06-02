'use client';

import React, { useEffect, useRef } from 'react';
import { MoStarEntityNode } from '@/types/mostar';

interface SigmaFlowLayerProps {
  map: any;
  nodes?: MoStarEntityNode[];
  isActive?: boolean;
}

interface Particle {
  lng: number;
  lat: number;
  speed: number;
  angle: number;
  life: number;
  maxLife: number;
}

export const SigmaFlowLayer: React.FC<SigmaFlowLayerProps> = ({ map, nodes, isActive = true }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);
  const particlesRef = useRef<Particle[]>([]);

  useEffect(() => {
    if (!map || !canvasRef.current || !isActive) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Sync Canvas Dimensions with Window/Map Wrapper
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initialize the Particle Array (focused over African continent)
    const PARTICLE_COUNT = 350;
    if (particlesRef.current.length === 0) {
      const initialParticles: Particle[] = [];
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        initialParticles.push({
          lng: -20 + Math.random() * 80,
          lat: -35 + Math.random() * 75,
          speed: 0.08 + Math.random() * 0.2,
          angle: Math.random() * Math.PI * 2,
          life: Math.random() * 100,
          maxLife: 60 + Math.random() * 120,
        });
      }
      particlesRef.current = initialParticles;
    }

    // Main WebGL-Synced Render Loop
    const drawFrame = () => {
      // Apply a slight opacity wash to create glowing trails
      ctx.fillStyle = 'rgba(5, 5, 5, 0.08)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Establish the Neon Cyan Glow Aesthetic
      ctx.strokeStyle = '#00ffcc';
      ctx.shadowBlur = 12;
      ctx.shadowColor = '#00ffcc';
      ctx.lineWidth = 1.2;
      ctx.beginPath();

      particlesRef.current.forEach((p) => {
        // MapLibre's built-in projection method converts geospatial math to screen coordinates
        const startPos = map.project([p.lng, p.lat]);

        // Update particle trajectory (Simulating fluid trade winds)
        p.lng += Math.cos(p.angle) * p.speed;
        p.lat += Math.sin(p.angle) * p.speed;
        p.angle += 0.015; // Smooth curving motion
        p.life++;

        const endPos = map.project([p.lng, p.lat]);

        // Render vector slice if it remains within the immediate view bounds
        if (
          startPos.x > 0 &&
          startPos.x < canvas.width &&
          startPos.y > 0 &&
          startPos.y < canvas.height
        ) {
          ctx.moveTo(startPos.x, startPos.y);
          ctx.lineTo(endPos.x, endPos.y);
        }

        // Recycle dead or drifted elements back onto the map grid
        if (
          p.life > p.maxLife ||
          p.lng > 60 ||
          p.lng < -20 ||
          p.lat > 40 ||
          p.lat < -40
        ) {
          p.lng = -20 + Math.random() * 80;
          p.lat = -35 + Math.random() * 75;
          p.life = 0;
          p.angle = Math.random() * Math.PI * 2;
        }
      });

      ctx.stroke();
      animationRef.current = requestAnimationFrame(drawFrame);
    };

    // Kickstart animation loop
    animationRef.current = requestAnimationFrame(drawFrame);

    // Handle Camera Interactivity Events
    const handleMapMove = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };

    map.on('move', handleMapMove);
    map.on('zoom', handleMapMove);
    map.on('rotate', handleMapMove);
    map.on('pitch', handleMapMove);

    // Cleanup on Component Unmount
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      map.off('move', handleMapMove);
      map.off('zoom', handleMapMove);
      map.off('rotate', handleMapMove);
      map.off('pitch', handleMapMove);
    };
  }, [map, isActive, nodes]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute top-0 left-0 w-full h-full pointer-events-none z-[5]"
      style={{ mixBlendMode: 'screen' }}
    />
  );
};
