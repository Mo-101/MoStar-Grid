MATCH (n) WHERE id(n) = 256
RETURN COUNT { (n)--() } AS shouldBeZero;
