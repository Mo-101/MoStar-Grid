import neo4j from 'neo4j-driver';

const uri = process.env.NEO4J_URI || 'bolt://localhost:7687';
const user = process.env.NEO4J_USER || 'neo4j';
const password = process.env.NEO4J_PASSWORD || 'mostar123';

if (!process.env.NEO4J_URI || !process.env.NEO4J_USER || !process.env.NEO4J_PASSWORD) {
  console.warn('Neo4j env vars missing in frontend runtime; using local defaults.');
}

export const driver = neo4j.driver(
  uri,
  neo4j.auth.basic(user, password),
  {
    maxConnectionLifetime: 3 * 60 * 60 * 1000,
    maxConnectionPoolSize: 50,
    connectionAcquisitionTimeout: 20000,
  }
);
