// preflight_phase1c_merge.cypher — read-only, no writes
// Corrected: match via internal id(n), not a nonexistent .id property. COUNT{} instead of size().

// 1) Confirm all expected pairs exist exactly once
UNWIND [
  {op:256, canon:910, name:'Ubuntu'},
  {op:257, canon:911, name:'Ukama'},
  {op:258, canon:912, name:'Ujamaa'},
  {op:259, canon:913, name:'Sankofa'},
  {op:260, canon:914, name:"Ma'at"},
  {op:261, canon:915, name:'Ntu'},
  {op:262, canon:916, name:'Hunhu/Unhu'},
  {op:263, canon:917, name:'Batho Pele'},
  {op:264, canon:918, name:'Harambee'},
  {op:265, canon:919, name:'Ujaama'},
  {op:266, canon:920, name:'Nia'},
  {op:267, canon:921, name:'Kujichagulia'},
  {op:268, canon:922, name:'Umoja'},
  {op:269, canon:923, name:'Ujima'},
  {op:270, canon:924, name:'Nia ya Jamii'},
  {op:271, canon:925, name:'Nommo'},
  {op:273, canon:927, name:'Kuumba'},
  {op:274, canon:928, name:'Imani'},
  {op:275, canon:929, name:'Communalism'},
  {op:276, canon:930, name:'Palaver'},
  {op:277, canon:931, name:'Mojo'},
  {op:278, canon:932, name:'Ashanti Stool'},
  {op:279, canon:933, name:'Mawu-Lisa'},
  {op:280, canon:934, name:'Odinani'},
  {op:281, canon:935, name:'Orisa'},
  {op:282, canon:936, name:'Vodun'}
] AS pair
OPTIONAL MATCH (op:Philosophy) WHERE id(op) = pair.op
OPTIONAL MATCH (canon:Philosophy) WHERE id(canon) = pair.canon
RETURN
  pair.op,
  pair.canon,
  pair.name,
  count(op)    AS op_count,
  count(canon) AS canon_count,
  op.core_principle    AS op_principle,
  canon.name           AS canon_name,
  canon.alt_names      AS canon_alt_names
ORDER BY pair.op;

// 2) Sanity check the hold node 272 and the missing canon gap 926
OPTIONAL MATCH (hold:Philosophy) WHERE id(hold) = 272
OPTIONAL MATCH (gap:Philosophy) WHERE id(gap) = 926
RETURN
  id(hold) AS hold_id,
  hold.core_principle AS hold_principle,
  hold.manifestation AS hold_manifestation,
  id(gap) AS canon_926_id,
  gap.name AS canon_926_name;

// 3) Relationship volume snapshot before merge
UNWIND [256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,273,274,275,276,277,278,279,280,281,282] AS opId
MATCH (n:Philosophy) WHERE id(n) = opId
RETURN opId AS operational_id, COUNT { (n)--() } AS degree
ORDER BY operational_id;

// 4) Check that each canon target actually carries the sovereign seal we must not disturb
UNWIND [910,911,912,913,914,915,916,917,918,919,920,921,922,923,924,925,927,928,929,930,931,932,933,934,935,936] AS cId
MATCH (n:Philosophy) WHERE id(n) = cId
RETURN cId AS canon_id, n.name AS name, n.mostar_sig IS NOT NULL AS has_sig, n.content_seal IS NOT NULL AS has_seal;
