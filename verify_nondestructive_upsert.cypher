MERGE (r:RetentionPolicy {id: 'RP_Telemetry_v1'})
SET r.domain          = coalesce(r.domain, 'Metric|BodyLayer|ExecutorHeartbeat|RuntimeEvent'),
    r.strategy         = coalesce(r.strategy, 'ARCHIVE_THEN_RELEASE'),
    r.archive_format   = coalesce(r.archive_format, 'jsonl.gz + sha256 manifest'),
    r.archive_location = coalesce(r.archive_location, 'PENDING_CONFIRMATION_SHOULD_NOT_APPEAR'),
    r.max_age_days     = coalesce(r.max_age_days, 30),
    r.immutable_flag   = coalesce(r.immutable_flag, false),
    r.reason           = coalesce(r.reason, 'placeholder_should_not_appear'),
    r.authored_by      = coalesce(r.authored_by, 'placeholder_should_not_appear'),
    r.created_at       = coalesce(r.created_at, datetime())
RETURN r { .* } AS policy;
