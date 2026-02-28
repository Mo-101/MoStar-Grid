"use client";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import styles from "./AfricanFlameMap.module.css";
import { useRef, useEffect } from "react";

/**
 * Represents a grid site with geographical coordinates and status information.
 */
export type GridSite = {
  name: string;
  lat: number;
  lon: number;
  glyph: string;
  status: string;
};

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || ""; // fallback safety

type FlameAtlasProps = {
  token: string;
  sites: GridSite[];
};

export default function FlameAtlas({ token, sites }: FlameAtlasProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  const INITIAL_VIEW = {
    longitude: 15,
    latitude: 2,
    zoom: 3,
  };

  useEffect(() => {
    if (!token || !mapContainer.current || map.current) return;
    
    mapboxgl.accessToken = token;
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [INITIAL_VIEW.longitude, INITIAL_VIEW.latitude],
      zoom: INITIAL_VIEW.zoom,
    });

    map.current.on("load", () => {
      console.log("Map loaded successfully");
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, [INITIAL_VIEW.latitude, INITIAL_VIEW.longitude, INITIAL_VIEW.zoom, token]);

  useEffect(() => {
    if (!map.current) return; // wait for map to initialize
    
    // Clear existing markers
    const markers = document.querySelectorAll('.mapboxgl-marker');
    markers.forEach(marker => marker.remove());

    sites.forEach((site) => {
      const el = document.createElement('div');
      el.className = styles.marker;
      
      const glyph = document.createElement('span');
      glyph.style.cssText = "font-size: 24px; filter: drop-shadow(0 0 8px rgba(255,165,0,0.8));";
      glyph.innerText = site.glyph;
      el.appendChild(glyph);

      const name = document.createElement('p');
      name.style.cssText = `
        margin: 4px 0 0;
        font-size: 10px;
        font-weight: bold;
        color: #fff;
        text-shadow: 0 0 4px #000;
        white-space: nowrap;
      `;
      name.innerText = site.name;
      el.appendChild(name);

      const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div style="padding: 8px; background: rgba(0,0,0,0.9); color: #fff; border-radius: 8px;">
          <h4 style="margin: 0 0 4px 0; color: #ff9800;">${site.glyph} ${site.name}</h4>
          <p style="margin: 4px 0 0; font-size: 12px; color: #aaa;">
            ${site.status}
          </p>
          <p style="margin: 4px 0 0; font-size: 10px; color: #666;">
            ${site.lat.toFixed(4)}, ${site.lon.toFixed(4)}
          </p>
        </div>
      `);

      new mapboxgl.Marker(el)
        .setLngLat([site.lon, site.lat])
        .setPopup(popup)
        .addTo(map.current!);
    });
  }, [sites]);

  if (!token) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", background: "rgba(0,0,0,0.8)", color: "#ff9800" }}>
        ⚠️ Missing Mapbox token
      </div>
    );
  }

  if (!sites?.length) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", background: "rgba(0,0,0,0.8)", color: "#aaa" }}>
        📭 No sites to map
      </div>
    );
  }

  return (
    <div 
      ref={mapContainer} 
      style={{ 
        width: "100%", 
        height: "100%", 
        minHeight: "400px",
        borderRadius: "12px",
        overflow: "hidden"
      }} 
    />
  );
}
