-- MoStar Grid Phase -1: runtime attestation and deep seal chain
CREATE SCHEMA IF NOT EXISTS grid;

CREATE TABLE IF NOT EXISTS grid.runtime_attestation (
    attestation_id UUID PRIMARY KEY,
    runtime_id TEXT NOT NULL,
    runtime_version TEXT NOT NULL,
    build_commit TEXT NOT NULL,
    runtime_digest TEXT NOT NULL UNIQUE,
    manifest JSONB NOT NULL,
    verification_status TEXT NOT NULL
        CHECK (verification_status IN ('verified', 'rejected', 'revoked')),
    verified_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS grid.runtime_seals (
    sequence BIGSERIAL PRIMARY KEY,
    attestation_id UUID NOT NULL REFERENCES grid.runtime_attestation(attestation_id),
    runtime_digest TEXT NOT NULL,
    previous_hash TEXT,
    seal_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
