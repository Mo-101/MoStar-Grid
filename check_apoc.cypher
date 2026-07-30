// check_apoc.cypher — read-only capability check
SHOW PROCEDURES YIELD name
WHERE name STARTS WITH 'apoc.refactor'
RETURN name ORDER BY name;
