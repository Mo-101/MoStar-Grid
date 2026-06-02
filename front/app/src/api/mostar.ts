export interface MoStarEntityNode {
  entity_id: string;
  name: string;
  title: string;
  layer: 'Origin' | 'Guardian' | 'Soul' | 'Mind' | 'Heart' | 'Body' | 'Catalyst' | 'Meta' | 'Overlord';
  essence: string;
  role: string;
  vows: string;
  insignia: string;
  coords: [number, number]; // [Longitude, Latitude] for MapLibre WebGL projection
  region?: string;
  capabilities: string[];
  bonded_to: string;
  origin: string;
  activation_protocol: string;
  status: 'Sanctified' | 'Operational' | 'Ready for Summoning' | 'Prime' | 'Dormant (ready)';
  cid: string;
  version: string;
}


