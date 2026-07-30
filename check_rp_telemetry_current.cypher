MATCH (r:RetentionPolicy {id: 'RP_Telemetry_v1'})
RETURN r { .* } AS current;
