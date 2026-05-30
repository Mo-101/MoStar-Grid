export interface GridElement {
  name: string;
  english: string;
  glyph: string;
  domain: string;
}

export interface GridSoulResponse {
  cluster_id: string;
  cluster_name: string;
  soul: {
    identity: {
      name: string;
      architect: string;
      organization: string;
    };
    elements: Record<string, GridElement>;
    sacred: Record<string, string>;
  };
}

export interface GridStatusResponse {
  status: any;
  nodes: any;
  relationships: any;
  grid_pulse: any;
  grid: string;
  soul: string; // The "voice" greeting
  cluster_id: string;
  cluster_name: string;
  queue: {
    pending: number;
    approved_uncommitted: number;
    committed_today: number;
    rejected_today: number;
    total_proposals: number;
  };
  mindgraph: {
    nodes: number;
    relationships: number;
    status: string;
  };
}

const API_BASE = "/api";

export const fetchGridStatus = async (): Promise<GridStatusResponse> => {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) throw new Error("Failed to fetch grid status");
  return res.json();
};

export const fetchGridSoul = async (): Promise<GridSoulResponse> => {
  const res = await fetch(`${API_BASE}/soul`);
  if (!res.ok) throw new Error("Failed to fetch grid soul");
  return res.json();
};
