"""
MoStar Grid — Sequential CSV Loader
Loads all CSVs into Neo4j one file at a time.
No linking. No relationships. Pure node ingestion.
Run: python load_all_csvs.py
"""

from neo4j import GraphDatabase
import sys

URI      = "bolt://localhost:7687"
USER     = "neo4j"
PASSWORD = "mostar123"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def run(session, label, query, stats_query):
    print(f"\n{'='*60}")
    print(f"  Loading: {label}")
    print(f"{'='*60}")
    result = session.run(query)
    summary = result.consume()
    print(f"  ✅ nodes created:  {summary.counters.nodes_created}")
    print(f"  ✅ props set:      {summary.counters.properties_set}")
    count = session.run(stats_query).single()[0]
    print(f"  📊 total in graph: {count}")

# ─────────────────────────────────────────────
# FILE BASE PATH (Neo4j LOAD CSV uses import/)
# ─────────────────────────────────────────────
BASE = "file:///data/csv/"

LOADERS = [

    # ── 1. IbibiioLanguageIntegration ──────────────────────
    (
        "ibibio_language_integration.csv → :IbibiioIntegration",
        f"""
        LOAD CSV WITH HEADERS FROM '{BASE}ibibio_language_integration.csv' AS row
        WITH row WHERE row.integration_id IS NOT NULL AND trim(row.integration_id) <> ''
        MERGE (n:IbibiioIntegration {{integration_id: trim(row.integration_id)}})
        SET
          n.component            = coalesce(trim(row.component), ''),
          n.ibibio_feature       = coalesce(trim(row.ibibio_feature), ''),
          n.implementation_status= coalesce(trim(row.implementation_status), ''),
          n.file_location        = coalesce(trim(row.file_location), ''),
          n.description          = coalesce(trim(row.description), ''),
          n.native_speakers      = coalesce(trim(row.native_speakers), ''),
          n.audio_files_count    = coalesce(trim(row.audio_files_count), ''),
          n.use_case             = coalesce(trim(row.use_case), '')
        """,
        "MATCH (n:IbibiioIntegration) RETURN count(n)"
    ),

    # ── 2. HealingPractice ─────────────────────────────────
    (
        "healing_practices.csv → :HealingPractice",
        f"""
        LOAD CSV WITH HEADERS FROM '{BASE}healing_practices.csv' AS row
        WITH row WHERE row.name IS NOT NULL AND trim(row.name) <> ''
        MERGE (n:HealingPractice {{name: trim(row.name)}})
        SET
          n.regions              = coalesce(trim(row.regions), ''),
          n.purpose              = coalesce(trim(row.purpose), ''),
          n.methods              = coalesce(trim(row.methods), ''),
          n.practitioners        = coalesce(trim(row.practitioners), ''),
          n.related_plants       = coalesce(trim(row.related_plants), ''),
          n.cultural_significance= coalesce(trim(row.cultural_significance), ''),
          n.related_philosophy   = coalesce(trim(row.related_philosophy), ''),
          n.spiritual_component  = coalesce(trim(row.spiritual_component), '')
        """,
        "MATCH (n:HealingPractice) RETURN count(n)"
    ),

    # ── 3. IfaMajorOdu ─────────────────────────────────────
    (
        "ifa_major_odu.csv → :IfaMajorOdu",
        f"""
        LOAD CSV WITH HEADERS FROM '{BASE}ifa_major_odu.csv' AS row
        WITH row WHERE row.name IS NOT NULL AND trim(row.name) <> ''
        MERGE (n:IfaMajorOdu {{name: trim(row.name)}})
        SET
          n.binary                  = coalesce(trim(row.binary), ''),
          n.number                  = coalesce(trim(row.number), ''),
          n.core_meaning            = coalesce(trim(row.core_meaning), ''),
          n.health_domain           = coalesce(trim(row.health_domain), ''),
          n.infrastructure_domain   = coalesce(trim(row.infrastructure_domain), ''),
          n.positive_manifestation  = coalesce(trim(row.positive_manifestation), ''),
          n.negative_manifestation  = coalesce(trim(row.negative_manifestation), ''),
          n.action_guidance         = coalesce(trim(row.action_guidance), '')
        """,
        "MATCH (n:IfaMajorOdu) RETURN count(n)"
    ),

    # ── 4. IfaOduSystem (256 Odu) ──────────────────────────
    (
        "ifa_odu_system.csv → :IfaOdu",
        f"""
        LOAD CSV WITH HEADERS FROM '{BASE}ifa_odu_system.csv' AS row
        WITH row WHERE row.odu_number IS NOT NULL AND trim(row.odu_number) <> ''
        MERGE (n:IfaOdu {{odu_number: toInteger(row.odu_number)}})
        SET
          n.binary_pattern   = coalesce(trim(row.binary_pattern), ''),
          n.name_yoruba      = coalesce(trim(row.name_yoruba), ''),
          n.name_english     = coalesce(trim(row.name_english), ''),
          n.interpretation   = coalesce(trim(row.interpretation), ''),
          n.ritual_context   = coalesce(trim(row.ritual_context), ''),
          n.symbolic_meaning = coalesce(trim(row.symbolic_meaning), ''),
          n.divination_use   = coalesce(trim(row.divination_use), ''),
          n.related_themes   = coalesce(trim(row.related_themes), '')
        """,
        "MATCH (n:IfaOdu) RETURN count(n)"
    ),

    # ── 5. IfaRule ─────────────────────────────────────────
    (
        "ifa_rules.csv → :IfaRule",
        f"""
        LOAD CSV WITH HEADERS FROM '{BASE}ifa_rules.csv' AS row
        WITH row WHERE row.odu_name IS NOT NULL AND trim(row.odu_name) <> ''
              AND row.domain IS NOT NULL AND trim(row.domain) <> ''
        MERGE (n:IfaRule {{odu_name: trim(row.odu_name), domain: trim(row.domain)}})
        SET
          n.binary_code      = coalesce(trim(row.binary_code), ''),
          n.odu_number       = coalesce(trim(row.odu_number), ''),
          n.core_meaning     = coalesce(trim(row.core_meaning), ''),
          n.priority_level   = coalesce(trim(row.priority_level), ''),
          n.indicators       = coalesce(trim(row.indicators), ''),
          n.positive_actions = coalesce(trim(row.positive_actions), ''),
          n.negative_actions = coalesce(trim(row.negative_actions), ''),
          n.keywords         = coalesce(trim(row.keywords), '')
        """,
        "MATCH (n:IfaRule) RETURN count(n)"
    ),

    # ── 6. IfaValidationScenario ───────────────────────────
    (
        "ifa_validation_validation_scenarios.csv → :IfaScenario",
        f"""
        LOAD CSV WITH HEADERS FROM '{BASE}ifa_validation_validation_scenarios.csv' AS row
        WITH row WHERE row.scenario_id IS NOT NULL AND trim(row.scenario_id) <> ''
        MERGE (n:IfaScenario {{scenario_id: toInteger(row.scenario_id)}})
        SET
          n.name              = coalesce(trim(row.name), ''),
          n.domain            = coalesce(trim(row.domain), ''),
          n.input_pattern     = coalesce(trim(row.input_pattern), ''),
          n.left_odu          = coalesce(trim(row.left_odu), ''),
          n.right_odu         = coalesce(trim(row.right_odu), ''),
          n.combined_odu      = coalesce(trim(row.combined_odu), ''),
          n.expected_decision = coalesce(trim(row.expected_decision), ''),
          n.expected_priority = coalesce(trim(row.expected_priority), ''),
          n.expected_outcome  = coalesce(trim(row.expected_outcome), ''),
          n.validation_criteria = coalesce(trim(row.validation_criteria), '')
        """,
        "MATCH (n:IfaScenario) RETURN count(n)"
    ),

]

print("\n🔥 MoStar Neo4j — Sequential CSV Loader")
print("   No linking. No tone. Just clean ingestion.\n")

with driver.session() as session:
    for label, query, stats_q in LOADERS:
        try:
            run(session, label, query, stats_q)
        except Exception as e:
            print(f"\n  ❌ ERROR loading {label}")
            print(f"     {e}")
            ans = input("  Continue to next file? [y/N]: ").strip().lower()
            if ans != 'y':
                print("  Stopping.")
                sys.exit(1)

print("\n\n✅ All CSV ingestion complete.")
print("   Next step: verify totals, then continue with remaining files.\n")
driver.close()
