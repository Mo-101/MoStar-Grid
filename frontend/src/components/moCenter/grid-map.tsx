'use client';

import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

export interface GridSignal {
  id: string;
  type: 'weather' | 'disease';
  coords: [number, number]; // [lng, lat]
  desc: string;
  region: string;
}

interface GridMapProps {
  signals: GridSignal[];
  onMapLoad?: (map: maplibregl.Map) => void;
}

export function GridMap({ signals, onMapLoad }: GridMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    // Initialize map
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [20.0, 0.0],
      zoom: 3.5,
      pitch: 45,
      bearing: -10,
      antialias: true,
      
    });

    map.current.on('load', () => {
      // Notify parent component that map is loaded
      if (onMapLoad) {
        onMapLoad(map.current!);
      }

      // Add signals to map
      signals.forEach((signal) => {
        // Create marker element
        const el = document.createElement('div');
        el.className = `w-5 h-5 rounded-full border-2 cursor-pointer transition-all ${
          signal.type === 'disease'
            ? 'bg-alert/20 border-alert pulse-glow-alert'
            : 'bg-primary/20 border-primary pulse-glow'
        }`;

        // Add marker to map
        const marker = new maplibregl.Marker({ element: el })
          .setLngLat(signal.coords)
          .setPopup(
            new maplibregl.Popup({ offset: 25 }).setHTML(`
              <div class="font-mono text-xs space-y-1">
                <strong>${signal.id}</strong>
                <br />
                ${signal.desc}
                <br />
                <em>${signal.region}</em>
              </div>
            `)
          )
          .addTo(map.current!);

        // Open popup on hover
        el.addEventListener('mouseenter', () => {
          marker.togglePopup();
        });
        el.addEventListener('mouseleave', () => {
          marker.togglePopup();
        });
      });
    });

    return () => {
      map.current?.remove();
    };
  }, [signals]);

  return (
    <div
      ref={mapContainer}
      className="absolute inset-0 w-full h-full"
      style={{ zIndex: 0 }}
    />
  );
}
