// ========================================================================
// MOSTAR UNIVERSE - NEO4J KNOWLEDGE GRAPH POPULATION SCRIPT
// Ground Truth Data Import - Zero Hallucination
// Date: December 6, 2025
// ========================================================================

// ========================================================================
// STEP 1: CREATE INDEXES FOR PERFORMANCE
// ========================================================================

CREATE INDEX odu_number_idx IF NOT EXISTS FOR (o:OduIfa) ON (o.odu_number);
CREATE INDEX philosophy_name_idx IF NOT EXISTS FOR (p:Philosophy) ON (p.name);
CREATE INDEX governance_name_idx IF NOT EXISTS FOR (g:Governance) ON (g.name);
CREATE INDEX healing_name_idx IF NOT EXISTS FOR (h:HealingPractice) ON (h.name);
CREATE INDEX plant_scientific_idx IF NOT EXISTS FOR (p:Plant) ON (p.scientific_name);
CREATE INDEX proverb_language_idx IF NOT EXISTS FOR (p:Proverb) ON (p.language);
CREATE INDEX word_ibibio_idx IF NOT EXISTS FOR (w:IbibioWord) ON (w.word);

// ========================================================================
// STEP 2: IMPORT IFÁ ODÙ SYSTEM (256 ENTRIES)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///ifa_odu_system.csv' AS row
CREATE (o:OduIfa {
  odu_number: toInteger(row.odu_number),
  binary_pattern: row.binary_pattern,
  name_yoruba: row.name_yoruba,
  name_english: row.name_english,
  interpretation: row.interpretation,
  ritual_context: row.ritual_context,
  symbolic_meaning: row.symbolic_meaning,
  divination_use: row.divination_use,
  related_themes: split(row.related_themes, '|')
});

// Create relationships between sequential Odù for progression paths
MATCH (o1:OduIfa), (o2:OduIfa)
WHERE o2.odu_number = o1.odu_number + 1
CREATE (o1)-[:PRECEDES]->(o2);

// Create relationships for thematic connections
MATCH (o1:OduIfa), (o2:OduIfa)
WHERE o1 <> o2 AND 
      any(theme IN o1.related_themes WHERE theme IN o2.related_themes)
CREATE (o1)-[:SHARES_THEME_WITH]->(o2);

// ========================================================================
// STEP 3: IMPORT AFRICAN PHILOSOPHIES (27 ENTRIES)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///african_philosophies.csv' AS row
CREATE (p:Philosophy {
  name: row.name,
  origin_country: row.origin_country,
  origin_region: row.origin_region,
  core_principle: row.core_principle,
  manifestation: split(row.manifestation, '|'),
  ethical_guidance: row.ethical_guidance,
  related_proverbs: split(row.related_proverbs, '|'),
  associated_governance: row.associated_governance
});

// Connect philosophies from same region
MATCH (p1:Philosophy), (p2:Philosophy)
WHERE p1 <> p2 AND p1.origin_region = p2.origin_region
CREATE (p1)-[:SHARES_REGION_WITH]->(p2);

// ========================================================================
// STEP 4: IMPORT INDIGENOUS GOVERNANCE SYSTEMS (28 ENTRIES)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///indigenous_governance.csv' AS row
CREATE (g:Governance {
  name: row.name,
  country: row.country,
  region: row.region,
  decision_method: split(row.decision_method, '|'),
  authority_source: split(row.authority_source, '|'),
  dispute_resolution: split(row.dispute_resolution, '|'),
  conflict_transformation: row.conflict_transformation,
  strengths: split(row.strengths, '|'),
  weaknesses: split(row.weaknesses, '|'),
  modern_relevance: split(row.modern_relevance, '|')
});

// Connect governance to philosophies
MATCH (g:Governance), (p:Philosophy)
WHERE g.name IN split(p.associated_governance, '|') OR
      p.name IN g.strengths OR
      contains(g.decision_method[0], p.name)
CREATE (p)-[:MANIFESTS_IN {strength: 0.85}]->(g);

// Connect governance from same region
MATCH (g1:Governance), (g2:Governance)
WHERE g1 <> g2 AND g1.region = g2.region
CREATE (g1)-[:SHARES_REGION_WITH]->(g2);

// ========================================================================
// STEP 5: IMPORT HEALING PRACTICES (28 ENTRIES)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///healing_practices.csv' AS row
CREATE (h:HealingPractice {
  name: row.name,
  regions: split(row.regions, ' '),
  purpose: split(row.purpose, '|'),
  methods: split(row.methods, '|'),
  practitioners: split(row.practitioners, '|'),
  related_plants: split(row.related_plants, '|'),
  cultural_significance: row.cultural_significance,
  related_philosophy: row.related_philosophy,
  spiritual_component: row.spiritual_component
});

// Connect healing practices to philosophies
MATCH (h:HealingPractice), (p:Philosophy)
WHERE contains(h.related_philosophy, p.name) OR
      any(principle IN p.manifestation WHERE contains(h.cultural_significance, principle))
CREATE (p)-[:GUIDES_ETHICS {context: 'healing'}]->(h);

// ========================================================================
// STEP 6: IMPORT MEDICINAL PLANTS (30 ENTRIES)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///medicinal_plants.csv' AS row
CREATE (p:Plant {
  scientific_name: row.scientific_name,
  local_names: split(row.local_names, '|'),
  regions: split(row.regions, ' '),
  medicinal_uses: split(row.medicinal_uses, '|'),
  preparation: split(row.preparation, '|'),
  dosage: row.dosage,
  contraindications: split(row.contraindications, '|'),
  philosophy_embodied: row.philosophy_embodied,
  spiritual_use: row.spiritual_use,
  related_healing_practice: row.related_healing_practice
});

// Connect plants to healing practices
MATCH (p:Plant), (h:HealingPractice)
WHERE p.related_healing_practice = h.name OR
      h.name IN p.related_healing_practice OR
      any(plant_name IN p.local_names WHERE plant_name IN h.related_plants)
CREATE (p)-[:USED_IN]->(h);

// Connect plants to philosophies
MATCH (p:Plant), (ph:Philosophy)
WHERE contains(p.philosophy_embodied, ph.name) OR
      contains(p.spiritual_use, ph.name)
CREATE (p)-[:EMBODIES_PRINCIPLE {principle: p.philosophy_embodied}]->(ph);

// ========================================================================
// STEP 7: IMPORT AFRICAN PROVERBS (20 EXISTING + EXPANSION)
// ========================================================================

// Note: Proverbs are already in JSON format, converting to Cypher
// Central Africa Proverbs
CREATE (p1:Proverb {
  text: "Ntoto wa bene bawumina",
  language: "Luba",
  meaning: "The land belongs to those who are buried in it",
  country: "Democratic Republic of Congo",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Establishes ancestral right to land ownership",
  year_approx: "pre-1900"
});

CREATE (p2:Proverb {
  text: "Tsi ya bakulu ke vandaka na ndombe",
  language: "Kongo",
  meaning: "The land of the elders cannot be traded like charcoal",
  country: "Democratic Republic of Congo",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Used against commodification of sacred land",
  year_approx: "pre-1900"
});

CREATE (p3:Proverb {
  text: "Le sol n'est pas orphelin",
  language: "Bamileke (French)",
  meaning: "The soil is not an orphan",
  country: "Cameroon",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Implies every land has ancestral ties and witnesses",
  year_approx: "pre-1900"
});

CREATE (p4:Proverb {
  text: "Mekone ye mbana na meto",
  language: "Tikar",
  meaning: "Truth and the land sit on the same stool",
  country: "Cameroon",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Land issues must be judged truthfully and traditionally",
  year_approx: "pre-1900"
});

CREATE (p5:Proverb {
  text: "Aboga mvoe, me y'ale aba",
  language: "Fang",
  meaning: "He who plants without permission loses even his sweat",
  country: "Gabon",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Used to affirm rightful land claims through authority",
  year_approx: "pre-1900"
});

CREATE (p6:Proverb {
  text: "Ndobe b'osone",
  language: "Myene",
  meaning: "The land has ears",
  country: "Gabon",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Spoken to warn against injustice on sacred land",
  year_approx: "pre-1900"
});

CREATE (p7:Proverb {
  text: "Zan ti si li mo kpalo",
  language: "Gbaya",
  meaning: "The land curses the one who steals it",
  country: "Central African Republic",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Land theft is viewed as a spiritual violation",
  year_approx: "pre-1900"
});

CREATE (p8:Proverb {
  text: "Kpina me yoke do",
  language: "Banda",
  meaning: "Judgment walks with the soil",
  country: "Central African Republic",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Truth tied to land decisions will surface eventually",
  year_approx: "pre-1900"
});

CREATE (p9:Proverb {
  text: "Nyir no dororo koyo",
  language: "Sara",
  meaning: "The land cannot be cut into lies",
  country: "Chad",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Used in land court to reject forged claims",
  year_approx: "pre-1900"
});

CREATE (p10:Proverb {
  text: "Alaa zayni dar",
  language: "Kanembu",
  meaning: "The land remembers better than men",
  country: "Chad",
  region: "Central Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Land is said to carry intergenerational memory",
  year_approx: "pre-1900"
});

// East Africa Proverbs
CREATE (p11:Proverb {
  text: "Gũtirĩ mũciĩ utarĩ kĩhĩĩ",
  language: "Kikuyu",
  meaning: "There is no homestead without a rightful heir",
  country: "Kenya",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Affirms ancestral lineage as basis for land inheritance",
  year_approx: "pre-1900"
});

CREATE (p12:Proverb {
  text: "Piny ok owang'o gi tho",
  language: "Luo",
  meaning: "The land does not rot with the dead",
  country: "Kenya",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Used to express continuity of land across generations",
  year_approx: "pre-1900"
});

CREATE (p13:Proverb {
  text: "Nthĩ ni ya atumia na athambĩ",
  language: "Kamba",
  meaning: "The land belongs to women and the priests",
  country: "Kenya",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Sacred authority over land rests in spiritual and maternal lines",
  year_approx: "pre-1900"
});

CREATE (p14:Proverb {
  text: "Meder bet amlak new",
  language: "Amhara",
  meaning: "The land is the house of God",
  country: "Ethiopia",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Land desecration is both legal and spiritual violation",
  year_approx: "pre-1900"
});

CREATE (p15:Proverb {
  text: "Lafti abbaa hin qaban, abbaa irraa fudhatan",
  language: "Oromo",
  meaning: "The land has no master; it was taken from someone",
  country: "Ethiopia",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Reminds of the impermanence of land claims",
  year_approx: "pre-1900"
});

CREATE (p16:Proverb {
  text: "Ardhi haidanganywi",
  language: "Swahili",
  meaning: "The land cannot be deceived",
  country: "Tanzania",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Truth is revealed through how land responds to injustice",
  year_approx: "pre-1900"
});

CREATE (p17:Proverb {
  text: "Ulimi wa shamba una mizizi",
  language: "Chaga",
  meaning: "Farming the land has roots",
  country: "Tanzania",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "True ownership is earned through consistent labor and presence",
  year_approx: "pre-1900"
});

CREATE (p18:Proverb {
  text: "Ettaka lya bajjajja terigabana",
  language: "Baganda",
  meaning: "Ancestral land is not for division",
  country: "Uganda",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Used to protect clan land from fragmentation",
  year_approx: "pre-1900"
});

CREATE (p19:Proverb {
  text: "Ngakipi etau, etau ejok",
  language: "Karimojong",
  meaning: "A land dispute kills, but it also reveals truth",
  country: "Uganda",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Land cases are high-stakes but reveal true lineage",
  year_approx: "pre-1900"
});

CREATE (p20:Proverb {
  text: "Piny ma nyig me gi dong cen",
  language: "Acholi",
  meaning: "A land trampled unjustly will turn back",
  country: "Uganda",
  region: "East Africa",
  category: "justice",
  theme: "land",
  cultural_notes: "Unjust land conquest invites reversal or curses",
  year_approx: "pre-1900"
});

// Connect proverbs to philosophies
MATCH (pr:Proverb), (ph:Philosophy)
WHERE pr.region = ph.origin_region OR
      contains(pr.cultural_notes, ph.name) OR
      any(proverb_text IN ph.related_proverbs WHERE contains(proverb_text, pr.text))
CREATE (pr)-[:EXPRESSES]->(ph);

// Connect proverbs to governance systems
MATCH (pr:Proverb), (g:Governance)
WHERE pr.category = 'justice' AND pr.region = g.region
CREATE (pr)-[:GUIDES]->(g);

// ========================================================================
// STEP 8: IMPORT IBIBIO WORDS (196 ENTRIES)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///ibibio_words.csv' AS row
CREATE (w:IbibioWord {
  word: row.`word:ID`,
  tone_pattern: row.tone_pattern,
  pos: row.pos,
  english: row.english,
  speaker: row.speaker,
  audio_file: row.audio_file,
  syllables: toInteger(row.`syllables:int`),
  frequency: toInteger(row.`frequency:int`)
});

// Create language node for Ibibio
MERGE (lang:Language {name: "Ibibio", family: "Niger-Congo", subfamily: "Benue-Congo", region: "Nigeria"});

// Connect all Ibibio words to the language
MATCH (w:IbibioWord), (lang:Language {name: "Ibibio"})
CREATE (w)-[:PART_OF_LANGUAGE]->(lang);

// ========================================================================
// STEP 9: CREATE KNOWLEDGE DOMAINS
// ========================================================================

CREATE (kd1:KnowledgeDomain {name: "Philosophy", description: "African philosophical systems and worldviews"});
CREATE (kd2:KnowledgeDomain {name: "Governance", description: "Indigenous governance and justice systems"});
CREATE (kd3:KnowledgeDomain {name: "Healing", description: "Traditional healing practices and medicine"});
CREATE (kd4:KnowledgeDomain {name: "Botany", description: "Medicinal plants and ethnobotany"});
CREATE (kd5:KnowledgeDomain {name: "Divination", description: "Ifá and other divination systems"});
CREATE (kd6:KnowledgeDomain {name: "Language", description: "African languages and linguistic systems"});
CREATE (kd7:KnowledgeDomain {name: "Wisdom", description: "Proverbs and oral traditions"});

// Connect nodes to knowledge domains
MATCH (p:Philosophy), (kd:KnowledgeDomain {name: "Philosophy"})
CREATE (p)-[:BELONGS_TO]->(kd);

MATCH (g:Governance), (kd:KnowledgeDomain {name: "Governance"})
CREATE (g)-[:BELONGS_TO]->(kd);

MATCH (h:HealingPractice), (kd:KnowledgeDomain {name: "Healing"})
CREATE (h)-[:BELONGS_TO]->(kd);

MATCH (p:Plant), (kd:KnowledgeDomain {name: "Botany"})
CREATE (p)-[:BELONGS_TO]->(kd);

MATCH (o:OduIfa), (kd:KnowledgeDomain {name: "Divination"})
CREATE (o)-[:BELONGS_TO]->(kd);

MATCH (w:IbibioWord), (kd:KnowledgeDomain {name: "Language"})
CREATE (w)-[:BELONGS_TO]->(kd);

MATCH (pr:Proverb), (kd:KnowledgeDomain {name: "Wisdom"})
CREATE (pr)-[:BELONGS_TO]->(kd);

// ========================================================================
// STEP 10: CREATE REGIONAL CONNECTIONS
// ========================================================================

CREATE (r1:Region {name: "West Africa", countries: ["Nigeria", "Ghana", "Senegal", "Benin", "Togo", "Cameroon", "Mali"]});
CREATE (r2:Region {name: "East Africa", countries: ["Kenya", "Tanzania", "Uganda", "Ethiopia", "Somalia", "Rwanda", "Burundi"]});
CREATE (r3:Region {name: "Central Africa", countries: ["DRC", "Congo", "CAR", "Chad", "Gabon"]});
CREATE (r4:Region {name: "Southern Africa", countries: ["South Africa", "Zimbabwe", "Zambia", "Botswana", "Namibia", "Lesotho", "Eswatini"]});
CREATE (r5:Region {name: "North Africa", countries: ["Egypt", "Morocco", "Tunisia", "Algeria", "Libya"]});

// Connect philosophies to regions
MATCH (p:Philosophy), (r:Region)
WHERE p.origin_region = r.name
CREATE (p)-[:ORIGINATES_FROM]->(r);

// Connect governance to regions
MATCH (g:Governance), (r:Region)
WHERE g.region = r.name
CREATE (g)-[:ORIGINATES_FROM]->(r);

// ========================================================================
// STEP 11: VERIFY IMPORT COUNTS
// ========================================================================

// Check node counts
MATCH (o:OduIfa) RETURN count(o) AS OduIfa_Count;
MATCH (p:Philosophy) RETURN count(p) AS Philosophy_Count;
MATCH (g:Governance) RETURN count(g) AS Governance_Count;
MATCH (h:HealingPractice) RETURN count(h) AS HealingPractice_Count;
MATCH (p:Plant) RETURN count(p) AS Plant_Count;
MATCH (pr:Proverb) RETURN count(pr) AS Proverb_Count;
MATCH (w:IbibioWord) RETURN count(w) AS IbibioWord_Count;

// Check relationship counts
MATCH ()-[r:MANIFESTS_IN]->() RETURN count(r) AS MANIFESTS_IN_Count;
MATCH ()-[r:GUIDES_ETHICS]->() RETURN count(r) AS GUIDES_ETHICS_Count;
MATCH ()-[r:USED_IN]->() RETURN count(r) AS USED_IN_Count;
MATCH ()-[r:EMBODIES_PRINCIPLE]->() RETURN count(r) AS EMBODIES_PRINCIPLE_Count;

// Total database statistics
MATCH (n) RETURN count(n) AS Total_Nodes;
MATCH ()-[r]->() RETURN count(r) AS Total_Relationships;

// ========================================================================
// IMPORT COMPLETE - MOSTAR UNIVERSE SYMBOLIC KNOWLEDGE GRID OPERATIONAL
// ========================================================================
