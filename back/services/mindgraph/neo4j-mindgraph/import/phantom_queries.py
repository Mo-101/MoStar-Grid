from neo4j import GraphDatabase

class PhantomQueries:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_risk_by_location(self, location: str, week_id: str):
        """
        Query 1: What's the risk in Maiduguri LGA this week?
        """
        query = """
        MATCH (c:CorridorNode {location: $location})-[:HAS_EPIDEMIOLOGICAL_RISK]->(r:EpiRiskNode {week_id: $week_id})
        RETURN c.name AS corridor_name, r.fireScore AS fire_score, r.diseaseFloor AS disease_floor, r.sealed AS sealed
        """
        with self.driver.session() as session:
            result = session.run(query, location=location, week_id=week_id)
            return [record.data() for record in result]

    def get_critical_corridors_by_impact(self, week_id: str):
        """
        Query 2: Which corridors are most critical to this forecast?
        """
        query = """
        MATCH (r:EpiRiskNode)-[inf:INFLUENCED_BY]->(s:SignalNode)
        WHERE r.week_id = $week_id
        RETURN s.type AS signal_type, count(inf) as impact_weight
        ORDER BY impact_weight DESC
        """
        with self.driver.session() as session:
            result = session.run(query, week_id=week_id)
            return [record.data() for record in result]

    def get_recent_model_drift(self, days: int = 30):
        """
        Query 3: Has the model drifted in the last 30 days?
        """
        query = """
        MATCH (r:EpiRiskNode)-[:DRIFT_DETECTED_IN]->(d:DriftWatchNode)
        WHERE datetime(r.timestamp) >= datetime().minus({days: $days})
        RETURN d.metric AS metric, d.severity AS severity, r.week_id AS week_id, d.detected_at AS detected_at
        ORDER BY d.detected_at DESC
        """
        with self.driver.session() as session:
            result = session.run(query, days=days)
            return [record.data() for record in result]

    def get_dissent_ledger(self):
        """
        Query 4: What did analysts disagree on?
        """
        query = """
        MATCH (c:CorridorNode)-[:HAS_EPIDEMIOLOGICAL_RISK]->(r:EpiRiskNode)-[:CHALLENGED_BY]->(d:DissentNode)
        RETURN c.location AS location, r.week_id AS week_id, d.analyst AS analyst, d.dissent_reason AS reason, d.timestamp AS timestamp
        ORDER BY d.timestamp DESC
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]
