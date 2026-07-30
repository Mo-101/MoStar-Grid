UNWIND [
  {op:257, canon:911}, {op:258, canon:912}, {op:259, canon:913}, {op:260, canon:914},
  {op:261, canon:915}, {op:262, canon:916}, {op:263, canon:917}, {op:264, canon:918},
  {op:265, canon:919}, {op:266, canon:920}, {op:267, canon:921}, {op:268, canon:922},
  {op:269, canon:923}, {op:270, canon:924}, {op:271, canon:925}, {op:273, canon:927},
  {op:274, canon:928}, {op:275, canon:929}, {op:276, canon:930}, {op:277, canon:931},
  {op:278, canon:932}, {op:279, canon:933}, {op:280, canon:934}, {op:281, canon:935},
  {op:282, canon:936}
] AS pair
MATCH (canon:Philosophy) WHERE id(canon) = pair.canon
MATCH (op:Philosophy) WHERE id(op) = pair.op
MATCH (op)-[old:BELONGS_TO]->(dom)
WITH canon, old, properties(old) AS oldProps, dom
CREATE (canon)-[new:BELONGS_TO]->(dom)
SET new = oldProps
RETURN count(new) AS created;
