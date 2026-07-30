// check_apoc_all.cypher — read-only capability check, full apoc surface
SHOW PROCEDURES YIELD name
WHERE name STARTS WITH 'apoc'
RETURN name ORDER BY name;
