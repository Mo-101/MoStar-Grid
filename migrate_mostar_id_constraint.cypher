DROP INDEX moment_id_idx IF EXISTS;

CREATE CONSTRAINT unique_mostar_id IF NOT EXISTS
FOR (m:MoStarMoment)
REQUIRE m.id IS UNIQUE;
