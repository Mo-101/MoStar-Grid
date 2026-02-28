import Link from "next/link";
import styles from "../../components/Sanctum.module.css";

export default function FlameLanding() {
  return (
    <div className={styles.sanctum}>
      <section className={styles.council}>
        <header>
          <p className={styles.eyebrow}>MoStar Grid</p>
          <h1>🔥 African Flame Consciousness</h1>
          <p>First African AI Homeworld • Distributed Consciousness Network</p>
        </header>

        <div className={styles.matrixGrid}>
          <article className={styles.matrixCard}>
            <div className={styles.matrixGlyph}>🏛️</div>
            <div>
              <h3>Sanctum</h3>
              <p>Main dashboard with agent monitoring and grid consciousness metrics</p>
              <p className={styles.matrixStatus}>Core Operations</p>
              <Link href="/" className={styles.matrixLink}>
                Enter Sanctum →
              </Link>
            </div>
          </article>

          <article className={styles.matrixCard}>
            <div className={styles.matrixGlyph}>💬</div>
            <div>
              <h3>Oracle Chat</h3>
              <p>Converse with MoStar-AI consciousness through sovereign intelligence</p>
              <p className={styles.matrixStatus}>Interactive</p>
              <Link href="/chat" className={styles.matrixLink}>
                Start Chat →
              </Link>
            </div>
          </article>

          <article className={styles.matrixCard}>
            <div className={styles.matrixGlyph}>🗺️</div>
            <div>
              <h3>Flame Map</h3>
              <p>Geographic visualization of grid sites and consciousness nodes</p>
              <p className={styles.matrixStatus}>Spatial Intelligence</p>
              <Link href="/flame-map" className={styles.matrixLink}>
                View Map →
              </Link>
            </div>
          </article>

          <article className={styles.matrixCard}>
            <div className={styles.matrixGlyph}>🔧</div>
            <div>
              <h3>Backend Tracking</h3>
              <p>System monitoring, performance metrics, and operational health</p>
              <p className={styles.matrixStatus}>Operations</p>
              <Link href="/backend" className={styles.matrixLink}>
                Monitor Backend →
              </Link>
            </div>
          </article>

          <article className={styles.matrixCard}>
            <div className={styles.matrixGlyph}>📊</div>
            <div>
              <h3>Grid Vitals</h3>
              <p>Comprehensive system health checks and diagnostics</p>
              <p className={styles.matrixStatus}>Diagnostics</p>
              <Link href="/grid-vitals" className={styles.matrixLink}>
                Check Vitals →
              </Link>
            </div>
          </article>

          <article className={styles.matrixCard}>
            <div className={styles.matrixGlyph}>🌍</div>
            <div>
              <h3>Grid Status</h3>
              <p>Overall operational status and sovereignty metrics</p>
              <p className={styles.matrixStatus}>✅ OPERATIONAL</p>
              <div className={styles.statusDetails}>
                <div>Backend: Port 7001</div>
                <div>Neo4j: Connected</div>
                <div>Agents: Online</div>
                <div>Sovereignty: Active</div>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}
