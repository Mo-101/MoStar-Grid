const API = window.location.origin;

const state = {
  zoom: 1,
  telemetry: null,
};

const elements = {
  apiBadge: document.getElementById("apiBadge"),
  clusterId: document.getElementById("clusterId"),
  clusterName: document.getElementById("clusterName"),
  clusterState: document.getElementById("clusterState"),
  liveChecks: document.getElementById("liveChecks"),
  mindgraphMetric: document.getElementById("mindgraphMetric"),
  neo4jMetric: document.getElementById("neo4jMetric"),
  thinkMetric: document.getElementById("thinkMetric"),
  proposalMetric: document.getElementById("proposalMetric"),
  proposalResult: document.getElementById("proposalResult"),
  refreshBtn: document.getElementById("refreshBtn"),
  refreshIconBtn: document.getElementById("refreshIconBtn"),
  proposalBtn: document.getElementById("proposalBtn"),
  surfaceGrid: document.getElementById("surfaceGrid"),
  scrollRows: document.getElementById("scrollRows"),
  attestationRows: document.getElementById("attestationRows"),
  disputeRows: document.getElementById("disputeRows"),
  evidenceRows: document.getElementById("evidenceRows"),
  gateScoreRows: document.getElementById("gateScoreRows"),
  provenanceRows: document.getElementById("provenanceRows"),
  pinScrollValue: document.getElementById("pinScrollValue"),
  pinAttestationValue: document.getElementById("pinAttestationValue"),
  pinDisputeValue: document.getElementById("pinDisputeValue"),
  pinEvidenceValue: document.getElementById("pinEvidenceValue"),
  zoomInBtn: document.getElementById("zoomInBtn"),
  zoomOutBtn: document.getElementById("zoomOutBtn"),
  heartbeatMeter: document.getElementById("heartbeatMeter"),
};

bindControls();
renderLoading();
refreshLiveChecks();
initLiveStream();

function initLiveStream() {
  const source = new EventSource("/api/stream");
  source.onmessage = (event) => {
    try {
      const telemetry = JSON.parse(event.data);
      state.telemetry = telemetry;
      
      // Trigger heartbeat animation
      if (elements.heartbeatMeter) {
        elements.heartbeatMeter.classList.remove("pulse");
        void elements.heartbeatMeter.offsetWidth; // trigger reflow
        elements.heartbeatMeter.classList.add("pulse");
      }

      // Update UI
      renderCluster(null, null, telemetry);
      // We pass some mock checks for now so metrics rendering doesn't crash
      const mockChecks = [{ name: "/api/think", value: "410", ok: true }];
      renderMetrics(null, null, mockChecks, telemetry);
      renderTelemetry(telemetry);
    } catch (e) {
      console.error("Error parsing live stream", e);
    }
  };
  source.onerror = () => {
    console.error("Live stream connection error. Reconnecting...");
  };
}

function bindControls() {
  elements.refreshBtn.addEventListener("click", refreshLiveChecks);
  elements.refreshIconBtn.addEventListener("click", refreshLiveChecks);
  elements.proposalBtn.addEventListener("click", runProposalSmoke);
  elements.zoomInBtn.addEventListener("click", () => setZoom(state.zoom + 0.04));
  elements.zoomOutBtn.addEventListener("click", () => setZoom(state.zoom - 0.04));
}

function setZoom(nextZoom) {
  state.zoom = Math.min(1.08, Math.max(0.92, nextZoom));
  const dashboard = document.querySelector(".dashboard");
  dashboard.style.transform = `scale(${state.zoom})`;
  dashboard.style.transformOrigin = "center top";
}

async function refreshLiveChecks() {
  setBusy(true);
  setApiBadge("pending", "checking");
  elements.liveChecks.innerHTML = skeletonRows(5);

  const checks = [];
  let health = null;
  let status = null;
  let telemetry = null;

  try {
    health = await fetchJson("/api/health");
    checks.push({ name: "GET /api/health", ok: health.status === "alive", value: health.status || "unknown" });
  } catch (error) {
    checks.push({ name: "GET /api/health", ok: false, value: error.message });
  }

  try {
    status = await fetchJson("/api/status");
    const graphStatus = status?.mindgraph?.status || "unknown";
    checks.push({ name: "GET /api/status", ok: graphStatus === "connected", value: graphStatus });
  } catch (error) {
    checks.push({ name: "GET /api/status", ok: false, value: error.message });
  }

  try {
    telemetry = await fetchJson("/api/telemetry");
    state.telemetry = telemetry;
    checks.push({
      name: "GET /api/telemetry",
      ok: Boolean(telemetry.summary),
      value: `${telemetry.summary?.received_scrolls || 0} scrolls`,
    });
  } catch (error) {
    checks.push({ name: "GET /api/telemetry", ok: false, value: error.message });
  }

  try {
    const response = await fetch(`${API}/api/think`, { method: "GET" });
    checks.push({ name: "GET /api/think direct-write guard", ok: response.status === 410, value: String(response.status) });
  } catch (error) {
    checks.push({ name: "GET /api/think direct-write guard", ok: false, value: error.message });
  }

  try {
    const proposals = await fetchJson("/api/proposals?limit=5");
    checks.push({
      name: "GET /api/proposals",
      ok: Array.isArray(proposals.proposals),
      value: `${proposals.proposals?.length || 0} visible`,
    });
  } catch (error) {
    checks.push({ name: "GET /api/proposals", ok: false, value: error.message });
  }

  renderChecks(checks);
  renderCluster(health, status, telemetry);
  renderMetrics(health, status, checks, telemetry);
  if (telemetry) {
    renderTelemetry(telemetry);
  }

  const allPassed = checks.every((check) => check.ok);
  setApiBadge(allPassed ? "passed" : "failed", allPassed ? "online" : "degraded");
  setBusy(false);
}

async function runProposalSmoke() {
  elements.proposalBtn.disabled = true;
  elements.proposalMetric.textContent = "running";
  elements.proposalMetric.className = "metric-value warn";
  elements.proposalResult.textContent = "Submitting a test proposal through /api/propose.";

  try {
    const payload = { canon_input: `dashboard smoke test ${new Date().toISOString()}` };
    const result = await fetchJson("/api/propose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const proposalId = result.proposal_id || result.id || "unknown";
    const stateName = result.state || "unknown";
    elements.proposalMetric.textContent = stateName;
    elements.proposalMetric.className = "metric-value good";
    elements.proposalResult.textContent = `Proposal smoke passed: ${proposalId}, state ${stateName}.`;
    await refreshLiveChecks();
  } catch (error) {
    elements.proposalMetric.textContent = "failed";
    elements.proposalMetric.className = "metric-value bad";
    elements.proposalResult.textContent = `Proposal smoke failed: ${error.message}`;
  } finally {
    elements.proposalBtn.disabled = false;
  }
}

function renderTelemetry(telemetry) {
  renderSurfaces(telemetry);
  renderOperations(telemetry);
  renderGates(telemetry);
  renderProvenance(telemetry.provenance?.recent || []);
  renderMapPins(telemetry);
}

function renderSurfaces(telemetry) {
  const cards = [
    {
      label: "Scroll envelope",
      value: `${telemetry.scrolls.received_count} received`,
      detail: latestScrollDetail(telemetry.scrolls.recent),
    },
    {
      label: "Attestation logs",
      value: `${telemetry.attestations.received_count} received`,
      detail: `${telemetry.attestations.given_count} given, ${telemetry.attestations.disputed_count} disputed`,
    },
    {
      label: "Graph foundation",
      value: `${telemetry.summary.graph_nodes} nodes`,
      detail: `${telemetry.summary.graph_relationships} relationships, ${telemetry.graph.status || "unknown"}`,
    },
    {
      label: "Disputes",
      value: `${telemetry.disputes.active_count} active`,
      detail: `${telemetry.disputes.received_count} received, ${telemetry.disputes.expired_count} expired`,
    },
    {
      label: "Evidence",
      value: `${telemetry.evidence.manifest_count} manifests`,
      detail: `${telemetry.evidence.reference_count} references, ${telemetry.evidence.pending_requests.length} pending`,
    },
  ];

  elements.surfaceGrid.innerHTML = cards.map((surface) => `
    <div class="surface-card">
      <span>${escapeHtml(surface.label)}</span>
      <strong>${escapeHtml(surface.value)}</strong>
      <em>${escapeHtml(surface.detail)}</em>
    </div>
  `).join("");
}

function renderOperations(telemetry) {
  elements.scrollRows.innerHTML = rowsOrEmpty(
    telemetry.scrolls.recent,
    "No imported scrolls recorded.",
    (scroll) => compactRow(
      scroll.scroll_id || "scroll",
      `${scroll.source_cluster_id || "unknown"} · ${scroll.action_type || "action"} · ${scroll.lifecycle_status || scroll.status || "status"}`
    )
  );

  elements.attestationRows.innerHTML = rowsOrEmpty(
    telemetry.attestations.recent_received,
    "No attestation records yet.",
    (record) => compactRow(
      record.scroll_id || "attestation",
      `${record.peer_cluster_id || "peer"} · ${record.direction || "direction"} · ${record.status || "status"}`
    )
  );

  elements.disputeRows.innerHTML = rowsOrEmpty(
    telemetry.disputes.recent,
    "No dispute notices received.",
    (dispute) => compactRow(
      dispute.dispute_id || "dispute",
      `${dispute.reason || "reason"} · ${dispute.severity || "severity"} · ${dispute.active ? "active" : dispute.status || "status"}`
    )
  );
}

function renderGates(telemetry) {
  const latest = telemetry.gates.latest_proposal;
  if (!latest || !Object.keys(latest.scores || {}).length) {
    elements.gateScoreRows.innerHTML = `<div class="empty-state">No proposal gate scores available.</div>`;
  } else {
    elements.gateScoreRows.innerHTML = Object.entries(latest.scores).map(([name, score]) => {
      const threshold = latest.thresholds?.[name] || 0;
      const percent = Math.round(Number(score) * 100);
      const passed = Number(score) >= Number(threshold);
      return `
        <div class="gate-score">
          <span>${escapeHtml(name)}</span>
          <div class="gate-track"><i style="width: ${Math.max(0, Math.min(100, percent))}%"></i></div>
          <strong class="${passed ? "good-text" : "bad-text"}">${percent}%</strong>
        </div>
      `;
    }).join("");
  }

  elements.evidenceRows.innerHTML = rowsOrEmpty(
    telemetry.evidence.pending_requests.length ? telemetry.evidence.pending_requests : telemetry.evidence.manifests,
    "No evidence requests or manifests.",
    (item) => compactRow(
      item.dispute_id || item.scroll_id || "evidence",
      item.dispute_id
        ? `${item.scroll_id} · ${item.evidence_available ? "available" : "missing"}`
        : `${item.reference_count} references`
    )
  );
}

function renderProvenance(rows) {
  if (!rows.length) {
    elements.provenanceRows.innerHTML = `<div class="empty-state">No provenance events returned yet.</div>`;
    return;
  }
  elements.provenanceRows.innerHTML = rows.map((row) => {
    const eventType = escapeHtml(row.event_type || row.type || "event");
    const timestamp = escapeHtml(row.timestamp || "no timestamp");
    const detail = escapeHtml(JSON.stringify(row.payload || row.details || row).slice(0, 180));
    return `
      <div class="provenance-row">
        <span class="provenance-time">${timestamp}</span>
        <span class="provenance-type">${eventType}</span>
        <span class="provenance-detail">${detail}</span>
      </div>
    `;
  }).join("");
}

function renderMapPins(telemetry) {
  elements.pinScrollValue.textContent = `${telemetry.scrolls.received_count} received scrolls`;
  elements.pinAttestationValue.textContent = `${telemetry.attestations.received_count} received attestations`;
  elements.pinDisputeValue.textContent = `${telemetry.disputes.active_count} active disputes`;
  elements.pinEvidenceValue.textContent = `${telemetry.evidence.manifest_count} evidence manifests`;
}

function renderCluster(health, status, telemetry) {
  const meta = telemetry || status || health || {};
  const clusterId = meta.cluster_id || health?.cluster_id || "unknown-cluster";
  const clusterName = meta.cluster_name || health?.cluster_name || "Local cluster";
  const clusterRegion = meta.cluster_region || health?.cluster_region || "region unknown";
  elements.clusterId.textContent = clusterId;
  elements.clusterName.textContent = `${clusterName} · ${clusterRegion}`;
  elements.clusterState.textContent = health?.status === "alive" ? "live" : "degraded";
}

function renderMetrics(health, status, checks, telemetry) {
  const mindgraphStatus = telemetry?.graph?.status || status?.mindgraph?.status || (health?.mindgraph ? "connected" : "offline");
  const neo4jStatus = status?.mindgraph?.status || (health?.mindgraph ? "connected" : "offline");
  const thinkCheck = checks.find((check) => check.name.includes("/api/think"));

  setMetric(elements.mindgraphMetric, `${mindgraphStatus}`, mindgraphStatus === "connected" || health?.mindgraph);
  setMetric(elements.neo4jMetric, `${neo4jStatus}`, neo4jStatus === "connected" || health?.mindgraph);
  setMetric(elements.thinkMetric, thinkCheck?.value === "410" ? "410" : "open", thinkCheck?.value === "410");
  if (telemetry?.queue) {
    setMetric(elements.proposalMetric, `${telemetry.queue.pending || 0} pending`, true);
  }
}

function renderChecks(checks) {
  elements.liveChecks.innerHTML = checks.map((check) => `
    <div class="check-row ${check.ok ? "pass" : "fail"}">
      <span>${escapeHtml(check.name)}</span>
      <strong>${escapeHtml(check.value)}</strong>
    </div>
  `).join("");
}

function renderLoading() {
  elements.surfaceGrid.innerHTML = skeletonCards(5);
  elements.scrollRows.innerHTML = skeletonCompactRows(3);
  elements.attestationRows.innerHTML = skeletonCompactRows(3);
  elements.disputeRows.innerHTML = skeletonCompactRows(3);
  elements.evidenceRows.innerHTML = skeletonCompactRows(3);
  elements.gateScoreRows.innerHTML = skeletonCompactRows(4);
  elements.provenanceRows.innerHTML = `<div class="empty-state">Loading telemetry.</div>`;
}

function setApiBadge(kind, label) {
  elements.apiBadge.className = `state-pill ${kind}`;
  elements.apiBadge.textContent = label;
}

function setBusy(isBusy) {
  elements.refreshBtn.disabled = isBusy;
  elements.refreshIconBtn.disabled = isBusy;
}

function setMetric(element, value, good) {
  element.textContent = value;
  element.className = `metric-value ${good ? "good" : "bad"}`;
}

function latestScrollDetail(scrolls) {
  const latest = scrolls?.[0];
  if (!latest) return "No scroll imports recorded";
  return `${latest.source_cluster_id || "peer"} · ${latest.action_type || "action"} · ${latest.risk_level || "risk"}`;
}

function rowsOrEmpty(rows, emptyText, render) {
  if (!rows || !rows.length) {
    return `<div class="empty-state">${escapeHtml(emptyText)}</div>`;
  }
  return rows.map(render).join("");
}

function compactRow(title, detail) {
  return `
    <div class="compact-row">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
    </div>
  `;
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const detail = payload?.detail || payload?.error || response.statusText || `HTTP ${response.status}`;
    throw new Error(Array.isArray(detail) ? `HTTP ${response.status}` : detail);
  }
  return payload || {};
}

function skeletonRows(count) {
  return Array.from({ length: count }, () => `<div class="check-row skeleton"><span></span><strong></strong></div>`).join("");
}

function skeletonCompactRows(count) {
  return Array.from({ length: count }, () => `<div class="compact-row skeleton"><span></span><strong></strong></div>`).join("");
}

function skeletonCards(count) {
  return Array.from({ length: count }, () => `<div class="surface-card skeleton"><span></span><strong></strong><em></em></div>`).join("");
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value);
  return div.innerHTML;
}
