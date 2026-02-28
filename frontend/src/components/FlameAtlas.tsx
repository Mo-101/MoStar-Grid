"use client";
import mapboxgl from "mapbox-gl";
<<<<<<< HEAD
<<<<<<< HEAD
import "mapbox-gl/dist/mapbox-gl.css";
import styles from "./AfricanFlameMap.module.css";
import { useRef, useEffect, useState } from "react";
=======
import styles from "./AfricanFlameMap.module.css";
import { useRef, useEffect } from "react";
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
import styles from "./AfricanFlameMap.module.css";
import { useRef, useEffect } from "react";
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88

/**
 * Represents a grid site with geographical coordinates and status information.
 */
export type GridSite = {
<<<<<<< HEAD
<<<<<<< HEAD
  name: string;
=======
  name:string;
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
  name:string;
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
  lat: number;
  lon: number;
  glyph: string;
  status: string;
};
<<<<<<< HEAD
<<<<<<< HEAD
=======
mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || ""; // fallback safety
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || ""; // fallback safety
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88

type FlameAtlasProps = {
  token: string;
  gridsites: GridSite[];
};

const INITIAL_VIEW = {
  longitude: 15,
  latitude: 2,
  zoom: 3,
};

export default function FlameAtlas({ token, gridsites }: FlameAtlasProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const map = useRef<mapboxgl.Map | null>(null);
<<<<<<< HEAD
<<<<<<< HEAD
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize map
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
      setMapLoaded(true);
    });

    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, [token]);

  // Add markers when map is loaded and gridsites change
  useEffect(() => {
    if (!map.current || !mapLoaded || !gridsites?.length) return;

    // Clear existing markers
    const markers = document.querySelectorAll(".mapboxgl-marker");
    markers.forEach((marker) => marker.remove());

    gridsites.forEach((site) => {
      const el = document.createElement("div");
      el.className = styles.marker || "flame-marker";
      el.style.cssText = `
        display: flex;
        flex-direction: column;
        align-items: center;
        cursor: pointer;
        transform: translate(-50%, -100%);
      `;

      const glyph = document.createElement("span");
      glyph.style.cssText = "font-size: 24px; filter: drop-shadow(0 0 8px rgba(255,165,0,0.8));";
      glyph.innerText = site.glyph;
      el.appendChild(glyph);

      const name = document.createElement("p");
      name.style.cssText = `
        margin: 4px 0 0 0;
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
          <p style="margin: 0; font-size: 12px; color: #aaa;">${site.status}</p>
          <p style="margin: 4px 0 0 0; font-size: 10px; color: #666;">
            ${site.lat.toFixed(4)}, ${site.lon.toFixed(4)}
          </p>
        </div>
      `);

      new mapboxgl.Marker(el)
        .setLngLat([site.lon, site.lat])
        .setPopup(popup)
        .addTo(map.current!);
    });
  }, [gridsites, mapLoaded]);

  if (!token) {
    return (
      <div className={styles.mapFallback} style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", background: "rgba(0,0,0,0.8)", color: "#ff9800" }}>
        ⚠️ Missing Mapbox token
      </div>
    );
  }

  if (!gridsites?.length) {
    return (
      <div className={styles.mapFallback} style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", background: "rgba(0,0,0,0.8)", color: "#aaa" }}>
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
=======
=======
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88

  if (!token) return <div>⚠️ Missing Mapbox token</div>;
  if (!gridsites?.length) return <div>📭 No sites to map</div>;

  useEffect(() => {
    if (map.current) return; // initialize map only once
    if (!mapContainer.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v9",
      center: [INITIAL_VIEW.longitude, INITIAL_VIEW.latitude],
      zoom: INITIAL_VIEW.zoom,
      accessToken: token,
    });
  }, [token]);

  useEffect(() => {
    if (!map.current) return; // wait for map to initialize

    // Clear existing markers
    const markers = document.querySelectorAll('.mapboxgl-marker');
    markers.forEach(marker => marker.remove());

    gridsites.forEach((site) => {
      const el = document.createElement('div');
      el.className = styles.marker;

      const span = document.createElement('span');
      span.innerText = site.glyph;
      el.appendChild(span);

      const p = document.createElement('p');
      p.innerText = site.name;
      el.appendChild(p);

      const small = document.createElement('small');
      small.innerText = site.status;
      el.appendChild(small);

      new mapboxgl.Marker(el)
        .setLngLat([site.lon, site.lat])
        .addTo(map.current!);
    });
  }, [gridsites]);


  return (
    <div ref={mapContainer} style={{ width: "100%", height: "100%" }} />
<<<<<<< HEAD
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
  );
};