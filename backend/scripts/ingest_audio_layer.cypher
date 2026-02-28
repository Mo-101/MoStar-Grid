// ── 1. Create AudioSample nodes ──────────────────────
LOAD CSV WITH HEADERS FROM 'file:///data/csv/audio_inventory.csv' AS row
WITH row WHERE row.filename IS NOT NULL
MERGE (a:AudioSample {filename: row.filename})
SET a.path = row.full_path,
    a.source = 'Ibibio_audio';

// ── 2. Create Speaker nodes ──────────────────────────
MERGE (s1:Speaker {name: 'Mfon Udoinyang'}) SET s1.code = 'MU';
MERGE (s2:Speaker {name: 'Itoro Ituen'}) SET s2.code = 'IT';

// ── 3. Link AudioSample to Speaker ───────────────────
LOAD CSV WITH HEADERS FROM 'file:///data/csv/audio_inventory.csv' AS row
WITH row WHERE row.filename IS NOT NULL AND row.speaker_code <> 'UNKNOWN'
MATCH (a:AudioSample {filename: row.filename})
MATCH (s:Speaker {code: row.speaker_code})
MERGE (a)-[:RECORDED_BY]->(s);

// ── 4. Final verification counts ─────────────────────
MATCH (a:AudioSample) WITH count(a) AS samples
MATCH (s:Speaker) WITH samples, count(s) AS speakers
MATCH ()-[r:RECORDED_BY]->() RETURN samples, speakers, count(r) AS relationships;
