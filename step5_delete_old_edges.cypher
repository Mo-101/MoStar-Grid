MATCH (op) WHERE id(op) = 256
MATCH (op)-[old:REFERENCES]-()
DELETE old;

MATCH (op) WHERE id(op) = 256
MATCH (op)-[old:BELONGS_TO]-()
DELETE old;
