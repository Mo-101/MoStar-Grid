"use client";
import mapboxgl from "mapbox-gl";
import styles from "./AfricanFlameMap.module.css";
import { useRef, useEffect } from "react";

/**
 * Represents a grid site with geographical coordinates and status information.
 */
export type GridSite = {
  name:string;
  lat: number;
  lon: number;
  glyph: string;
  status: string;
};
mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || ""; // fallback safety

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
  );
};