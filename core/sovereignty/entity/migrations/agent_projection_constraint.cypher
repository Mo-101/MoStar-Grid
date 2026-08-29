// Schema invariant for MindProjector agent projection.
// Ensures MERGE on :Agent {id: ...} is backed by a uniqueness guarantee,
// preventing duplicate node creation under concurrent projection.
CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
  FOR (a:Agent)
  REQUIRE a.id IS UNIQUE;
