"use client";

import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import GridNav from "./GridNav";

// Use environment variable for token
mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

export default function AfricanFlameMap() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    if (!mapboxgl.accessToken) {
      setError("Mapbox token is missing. Please add NEXT_PUBLIC_MAPBOX_TOKEN to your .env.local file.");
      return;
    }

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: "mapbox://styles/akanimo1/cmm97dp5s004d01r66rs82x6j",
        center: [-22.834786, -9.021783], // Center globe
        zoom: 1.98,
        pitch: 1.01, // Tilt for 3D effect
        bearing: 0,
        projection: "globe" as any, // Use globe projection
      });

      map.current.on("style.load", () => {
        // Add minimal atmosphere effect
        map.current?.setFog({
          color: "rgb(6, 7, 11)", // Lower atmosphere
          "high-color": "rgb(4, 10, 20)", // Upper atmosphere
          "horizon-blend": 0.05, // Atmosphere thickness
          "space-color": "rgb(1, 3, 8)", // Background color
          "star-intensity": 0.15 // Background star brightness
        });

        // Enable 3D Terrain
        if (!map.current?.getSource('mapbox-dem')) {
          map.current?.addSource('mapbox-dem', {
            'type': 'raster-dem',
            'url': 'mapbox://mapbox.mapbox-terrain-dem-v1',
            'tileSize': 512,
            'maxzoom': 1.01
          });
        }
        map.current?.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });

        // Spin the globe
        spinGlobe();
      });

      // User interaction state
      let userInteracting = false;
      const spinEnabled = true;

      const spinGlobe = () => {
        if (!map.current) return;
        const zoom = map.current.getZoom();
        if (spinEnabled && !userInteracting && zoom < 5) {
          let distancePerSecond = 360 / 120; // One revolution per 120 seconds
          if (zoom > 3) {
            const zoomDif = (5 - zoom) / (5 - 3);
            distancePerSecond *= zoomDif;
          }
          const center = map.current.getCenter();
          center.lng -= distancePerSecond;
          // Smoothly animate the map over one second.
          map.current.easeTo({ center, duration: 1000, easing: (n) => n });
        }
      };

      // Pause spinning on interaction
      map.current.on("mousedown", () => { userInteracting = true; });
      map.current.on("touchstart", () => { userInteracting = true; });

      // Restart spinning the globe when interaction is complete
      const resumeSpin = () => {
        userInteracting = false;
        spinGlobe();
      };

      map.current.on("mouseup", resumeSpin);
      map.current.on("touchend", resumeSpin);
      map.current.on("dragend", resumeSpin);
      map.current.on("pitchend", resumeSpin);
      map.current.on("rotateend", resumeSpin);

      // When animation is complete, start spinning again
      map.current.on("moveend", () => {
        spinGlobe();
      });

      map.current.on("error", (e) => {
        console.error("Mapbox error:", e);
        if (e.error?.message?.includes("Unauthorized") || e.error?.message?.includes("Token")) {
          setError("Invalid or missing Mapbox token: " + e.error.message);
        } else {
          setError(e.error?.message || "Map loading error");
        }
      });
    } catch (err) {
      setError("Failed to initialize map. Please check your Mapbox token and internet connection.");
      console.error(err);
    }

    // Cleanup on unmount
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  return (
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, overflow: "hidden", background: "#010308" }}>
      {/* Absolute positioning for the map container */}
      <div ref={mapContainer} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />

      {/* Global Navigation Overlay */}
      <div style={{ position: "absolute", top: 16, right: 20, zIndex: 100, width: "calc(100% - 40px)", display: "flex", justifyContent: "flex-end", pointerEvents: "none" }}>
        <div style={{ pointerEvents: "all" }}>
          <GridNav />
        </div>
      </div>

      {/* Title / Info Overlay */}
      <div style={{ position: "absolute", top: 16, left: 20, zIndex: 20, display: "flex", alignItems: "center", gap: 10, pointerEvents: "none" }}>
        <div style={{ background: "rgba(0,0,0,0.65)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: "9px 16px", backdropFilter: "blur(12px)" }}>
          <div style={{ color: "#fff", fontSize: 13, fontWeight: 700, letterSpacing: 0.4, display: "flex", alignItems: "center", gap: 6 }}>
            <span>🔥</span> African Flame Grid Overview
          </div>
          <div style={{ color: "rgba(255,255,255,0.38)", fontSize: 10, marginTop: 2 }}>
            Sovereign Nodes · Real-time Topography · Global Witness
          </div>
        </div>
      </div>

      {/* Error Overlay */}
      {error && (
        <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", zIndex: 200, background: "rgba(0,0,0,0.85)", border: "1px solid #ef4444", borderRadius: 12, padding: "20px", textAlign: "center", minWidth: 300 }}>
          <h3 style={{ color: "#ef4444", marginBottom: 10, fontSize: 16 }}>Map Initialization Error</h3>
          <p style={{ color: "rgba(255,255,255,0.8)", fontSize: 14 }}>{error}</p>
        </div>
      )}
    </div>
  );
}