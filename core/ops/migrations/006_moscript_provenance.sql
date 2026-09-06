CREATE SCHEMA IF NOT EXISTS provenance;

CREATE TABLE IF NOT EXISTS provenance.moscript_receipts (
    attestation_id UUID PRIMARY KEY,
    execution_id UUID NOT NULL,
    runtime_id TEXT NOT NULL,
    sequence_no BIGINT NOT NULL,
    previous_receipt_hash TEXT,
    receipt_hash TEXT NOT NULL UNIQUE,
    key_id TEXT NOT NULL,
    signature_algorithm TEXT NOT NULL,
    signature TEXT NOT NULL,
    receipt JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (runtime_id, sequence_no)
);

CREATE TABLE IF NOT EXISTS provenance.moscript_chain_heads (
    runtime_id TEXT PRIMARY KEY,
    sequence_no BIGINT NOT NULL,
    receipt_hash TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
