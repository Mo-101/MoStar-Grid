import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/grid/parts";

/**
 * MoScripts — the Home of Glyphs.
 *
 * Rendered natively in the Grid's own design system (cyan HUD structure, gold
 * reserved for canonical glyph surfaces) rather than as an HTML string inside
 * an iframe. The previous version framed its markup with
 * `sandbox="allow-same-origin allow-scripts"`, a pairing that lets framed
 * content reach back into the parent origin — nothing here needs a frame.
 */

const BASE_ELEMENTS = [
  { glyph: "🜂", name: "Ikang", element: "Fire", role: "signal ignition" },
  { glyph: "🜄", name: "Mmọng", element: "Water", role: "displacement flow" },
  { glyph: "🜁", name: "Afim", element: "Air", role: "language transmission" },
  { glyph: "🜃", name: "Isong", element: "Earth", role: "terrain memory" },
] as const;

const GLYPHS = [
  ["🜀", "A"],
  ["🜁", "B · Air"],
  ["🜂", "C · Fire"],
  ["🜃", "D · Earth"],
  ["🜄", "E · Water"],
  ["🜅", "F"],
  ["🜆", "G"],
  ["🜇", "H"],
  ["🜈", "I"],
  ["🜉", "J"],
  ["🜊", "K"],
  ["🜋", "L"],
  ["🜌", "M"],
  ["🜍", "N"],
  ["🜎", "O"],
  ["🜏", "P"],
  ["🜐", "Q"],
  ["🜑", "R"],
  ["🜒", "S"],
  ["🜓", "T"],
  ["🜔", "U"],
  ["🜕", "V"],
  ["🜖", "W"],
  ["🜗", "X"],
  ["🜘", "Y"],
  ["🜙", "Z"],
  ["🜚", "0"],
  ["🜛", "1"],
  ["🜜", "2"],
  ["🜝", "3"],
  ["🜞", "4"],
  ["🜟", "5"],
  ["🜠", "6"],
  ["🜡", "7"],
  ["🜢", "8"],
  ["🜣", "9"],
  ["🜤", "→ gate"],
  ["🜥", "≥ floor"],
  ["🜦", "· join"],
  ["🜧", "[ open"],
  ["🜨", "] close"],
  ["🜩", ": define"],
] as const;

const PRINCIPLES = [
  {
    eyebrow: "Discover",
    title: 'Exact-case tag: "MoScripts"',
    body: "The Grid locates candidate MoScripts blocks by canonical identity rather than filename, provider, runtime, or service.",
  },
  {
    eyebrow: "Validate",
    title: "Schema before execution",
    body: "A tag is a locator, not proof. Candidate blocks must satisfy the canonical MoScripts schema before they become executable law.",
  },
  {
    eyebrow: "Bind",
    title: "Digest-backed lineage",
    body: "Source digests bind MoScripts law to registry records and runtime implementations so drift is visible instead of silently accepted.",
  },
  {
    eyebrow: "Execute",
    title: "Governed runtime only",
    body: "MoScripts defines the law. TypeScript, Python, Cypher, WASM or future runtimes implement it under the Grid's permissions and provenance.",
  },
] as const;

const DOMAINS = [
  ["Mind Conduit", "Binding, retrieval, provenance and attestation guards"],
  ["Governance", "Adjudication, promotion, permission and covenant controls"],
  ["DeepCAL", "Decision rituals, uncertainty handling and governed analysis"],
  ["Woo", "MoScript-bound intelligence and interaction flows"],
  ["MCP", "Tool and service invocation contracts"],
  ["Senses", "Weather, health, voice and future evidence-bearing inputs"],
] as const;

const FLOW = [
  ["01", "Locate", 'Find candidate blocks carrying tag: "MoScripts".'],
  ["02", "Validate", "Parse and verify the canonical schema; reject malformed identity."],
  ["03", "Digest", "Compute deterministic source identity for lineage and drift detection."],
  ["04", "Register", "Resolve stable ID, owner, kind and implementation references."],
  ["05", "Bind", "Attach runtime implementation and applicable constitutional authority."],
  ["06", "Execute", "Run only through the governed Grid path; record provenance and effects."],
] as const;

const MOSCRIPT_SAMPLE = `{
  tag: "MoScripts",
  id: "mo-mind-provenance-filter-001",
  schema_version: "1.0.0",
  owner: {
    application: "MoStar Grid",
    service: "Mind Conduit"
  },
  kind: "guard",
  provenance: {
    source_digest: "<deterministic>",
    constitution_hash: "<bound>"
  }
}`;

const GLYPH_SAMPLE = `🜂🜦🜂🜄🜁🜃🜦🜚🜚🜛
🜂🜩🜁🜈🜊🜀🜍🜆
🜒🜎🜔🜑🜂🜩🜂🜄🜁🜓🜈🜍🜄🜋
🜓🜑🜔🜒🜓🜩🜢🜦🜢🜡
🜋🜀🜖🜩🜟🜦🜡🜚
🜖🜎🜎🜧🜓🜑🜔🜒🜓🜥🜟🜦🜡🜚🜨
🜤🜁🜂🜓🜈🜕🜀🜓🜄`;

export const Route = createFileRoute("/moscript")({
  head: () => ({
    meta: [
      { title: "Home of Glyphs — MoScripts · MoStar Grid" },
      {
        name: "description",
        content:
          "MoScripts — the Home of Glyphs: discoverable, schema-validated, provenance-bound executable law for the MoStar Grid.",
      },
    ],
  }),
  component: Page,
});

function Kicker({
  children,
  tone = "cyan",
}: {
  children: React.ReactNode;
  tone?: "cyan" | "gold";
}) {
  return (
    <div
      className={`text-[10px] tracking-[0.24em] uppercase ${
        tone === "gold" ? "neon-text-gold" : "text-[var(--color-neon-cyan)]"
      }`}
    >
      {children}
    </div>
  );
}

function SectionHeader({
  eyebrow,
  title,
  copy,
  tone = "cyan",
}: {
  eyebrow: string;
  title: string;
  copy?: string;
  tone?: "cyan" | "gold";
}) {
  return (
    <div className="mb-5 grid items-end gap-4 border-b border-white/10 pb-4 xl:grid-cols-[1fr_minmax(0,520px)]">
      <div>
        <Kicker tone={tone}>{eyebrow}</Kicker>
        <h2 className="mt-2 text-xl font-semibold tracking-[0.06em] text-[var(--foreground)] sm:text-2xl">
          {title}
        </h2>
      </div>
      {copy ? <p className="text-xs leading-6 text-[var(--muted-foreground)]">{copy}</p> : null}
    </div>
  );
}

function Page() {
  return (
    <PageShell active="moscript">
      <div className="space-y-10">
        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <section className="panel panel-corners relative overflow-hidden rounded-md px-5 py-7 sm:px-8 sm:py-10">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-[var(--color-neon-cyan)]/70" />
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.18]"
            style={{
              backgroundImage:
                "linear-gradient(rgba(0,216,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(0,216,255,0.10) 1px, transparent 1px)",
              backgroundSize: "42px 42px",
              maskImage: "linear-gradient(to bottom, black, transparent 84%)",
            }}
            aria-hidden="true"
          />

          <div className="relative grid items-center gap-10 lg:grid-cols-[1.3fr_0.7fr]">
            <div>
              <span className="inline-flex items-center gap-2 rounded-sm border border-[var(--color-neon-gold)]/40 bg-[oklch(0.24_0.07_80/0.2)] px-2.5 py-1 text-[10px] tracking-[0.2em] uppercase neon-text-gold">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-neon-gold)] shadow-[0_0_10px_var(--color-neon-gold)]" />
                MoScripts · Home of Glyphs
              </span>

              <h1 className="mt-6 max-w-3xl text-4xl leading-[0.98] font-semibold tracking-[-0.02em] text-[var(--foreground)] sm:text-6xl">
                The Grid&apos;s law,
                <br />
                written in <span className="neon-text-gold">living symbols.</span>
              </h1>

              <p className="mt-5 max-w-2xl text-sm leading-7 text-[var(--muted-foreground)]">
                MoScripts is the governed language layer of the MoStar Grid: discoverable by
                canonical tag, validated by schema, bound by digest, registered by identity, and
                executed only through governed runtime paths.
              </p>

              <div className="mt-6 border-l-2 border-[var(--color-neon-cyan)] pl-4 text-xs leading-6 text-[var(--foreground)]">
                The model is replaceable intelligence. The Grid is the sovereign mind. MoScripts is
                part of the law that binds intelligence to that mind.
              </div>
            </div>

            <div
              className="relative mx-auto grid aspect-square w-full max-w-[300px] place-items-center rounded-full border border-[var(--color-neon-gold)]/35"
              style={{
                background:
                  "radial-gradient(circle, oklch(0.24 0.07 80 / 0.34), oklch(0.24 0.07 80 / 0.06) 48%, transparent 69%)",
                boxShadow: "inset 0 0 70px rgba(246,196,83,0.10), 0 0 80px rgba(246,196,83,0.08)",
              }}
              aria-label="MoScripts glyph seal"
            >
              <div className="pointer-events-none absolute inset-[12%] rounded-full border border-[var(--color-neon-gold)]/22" />
              <div className="pointer-events-none absolute inset-[26%] rounded-full border border-[var(--color-neon-gold)]/22" />
              <div className="text-[clamp(74px,11vw,128px)] leading-none neon-text-gold">🜂</div>
              <div className="absolute bottom-[13%] rounded-sm border border-[var(--color-neon-gold)]/40 bg-[oklch(0.13_0.02_250/0.7)] px-2 py-1 text-[9px] tracking-[0.16em] uppercase neon-text-gold">
                tag: &quot;MoScripts&quot;
              </div>
            </div>
          </div>
        </section>

        {/* ── Identity model ───────────────────────────────────────────── */}
        <section
          className="grid gap-px overflow-hidden rounded-md border border-white/10 bg-white/10 sm:grid-cols-2 xl:grid-cols-4"
          aria-label="MoScripts identity model"
        >
          {[
            ["Locate", "Exact-case canonical tag"],
            ["Prove", "Schema + deterministic digest"],
            ["Bind", "Registry + implementation lineage"],
            ["Govern", "Permissions + provenance + runtime"],
          ].map(([label, body]) => (
            <div key={label} className="bg-[oklch(0.115_0.025_250)] p-4">
              <div className="text-[10px] tracking-[0.2em] uppercase text-[var(--color-neon-cyan)]">
                {label}
              </div>
              <div className="mt-2 text-xs leading-5 text-[var(--muted-foreground)]">{body}</div>
            </div>
          ))}
        </section>

        {/* ── Constitutional identity ──────────────────────────────────── */}
        <section>
          <SectionHeader
            eyebrow="Constitutional identity"
            title="One tag. Many runtimes."
            copy='The exact-case tag "MoScripts" is how the Grid discovers candidate MoScripts blocks across applications and services. Discovery starts with the tag; trust starts only after schema validation and provenance checks.'
          />
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {PRINCIPLES.map((item) => (
              <article
                key={item.eyebrow}
                className="rounded-md border border-white/10 bg-white/[0.025] p-4 transition-colors hover:border-[var(--color-neon-cyan)]/40 hover:bg-white/[0.045]"
              >
                <div className="text-[9px] tracking-[0.18em] uppercase text-[var(--color-neon-cyan)]">
                  {item.eyebrow}
                </div>
                <h3 className="mt-3 text-sm font-semibold tracking-[0.04em] text-[var(--foreground)]">
                  {item.title}
                </h3>
                <p className="mt-2 text-xs leading-6 text-[var(--muted-foreground)]">{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ── Glyph foundation ─────────────────────────────────────────── */}
        <section>
          <SectionHeader
            eyebrow="Glyph foundation"
            tone="gold"
            title="Four roots. Expanding expression."
            copy="The glyph layer is a symbolic substrate for MoScripts expression. The registry — not visual similarity or secrecy — remains authoritative for meaning."
          />
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {BASE_ELEMENTS.map((element) => (
              <article
                key={element.name}
                className="flex min-h-36 flex-col justify-between rounded-md border border-white/10 bg-[oklch(0.125_0.03_75/0.35)] p-4"
              >
                <div className="text-4xl leading-none neon-text-gold">{element.glyph}</div>
                <div className="mt-4">
                  <strong className="block text-sm font-semibold tracking-[0.04em] text-[var(--foreground)]">
                    {element.name} · {element.element}
                  </strong>
                  <small className="mt-1 block text-[10px] tracking-[0.1em] text-[var(--muted-foreground)]">
                    {element.role}
                  </small>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* ── Glyph atlas ──────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            eyebrow="Glyph atlas"
            tone="gold"
            title="The working symbol field."
            copy="This page is the Home of Glyphs: a human-facing atlas and discovery surface. Canonical glyph semantics belong in the MoScripts registry and validator, not in UI labels alone."
          />

          <div className="grid grid-cols-[repeat(auto-fill,minmax(74px,1fr))] gap-2">
            {GLYPHS.map(([glyph, label]) => (
              <div
                key={`${glyph}-${label}`}
                className="grid min-h-[76px] place-items-center content-center rounded-md border border-white/10 bg-white/[0.025] transition-[transform,border-color] duration-150 hover:-translate-y-0.5 hover:border-[var(--color-neon-gold)]/45"
              >
                <b className="text-2xl leading-tight font-normal neon-text-gold">{glyph}</b>
                <span className="mt-1 text-[8px] tracking-[0.08em] uppercase text-[var(--muted-foreground)]">
                  {label}
                </span>
              </div>
            ))}
          </div>

          <p className="mt-3 text-[10px] leading-6 text-[var(--muted-foreground)]">
            <strong className="text-[var(--foreground)]">Important:</strong> this atlas can expose a
            working or partial mapping without making the UI the source of truth. The canonical
            registry should own stable meanings, versions and lineage.
          </p>
        </section>

        {/* ── Schema ───────────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            eyebrow="Schema"
            title='The Grid recognizes "MoScripts".'
            copy="A canonical block identifies itself. Filename, directory, implementation language and provider are not constitutional identity."
          />

          <div className="grid gap-3 lg:grid-cols-2">
            <div className="overflow-hidden rounded-md border border-white/10 bg-[oklch(0.09_0.02_250)]">
              <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3 text-[9px] tracking-[0.16em] uppercase text-[var(--muted-foreground)]">
                <span>Canonical block identity</span>
                <b className="font-medium text-[var(--color-neon-cyan)]">MoScripts</b>
              </div>
              <pre className="m-0 min-h-[300px] overflow-auto p-5 font-mono text-xs leading-7 whitespace-pre-wrap text-[var(--foreground)]">
                {MOSCRIPT_SAMPLE}
              </pre>
            </div>

            <div className="overflow-hidden rounded-md border border-white/10 bg-[oklch(0.09_0.02_250)]">
              <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3 text-[9px] tracking-[0.16em] uppercase text-[var(--muted-foreground)]">
                <span>Glyph expression</span>
                <b className="font-medium neon-text-gold">symbolic form</b>
              </div>
              <pre className="m-0 flex min-h-[300px] items-center overflow-auto p-5 text-[17px] leading-8 tracking-[0.025em] whitespace-pre-wrap neon-text-gold">
                {GLYPH_SAMPLE}
              </pre>
            </div>
          </div>
        </section>

        {/* ── Registry path ────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            eyebrow="Registry path"
            title="Locate → validate → bind → execute."
            copy="The tag is deliberately simple. The trust chain is not. Each stage removes ambiguity before executable law reaches the runtime."
          />

          <div className="grid gap-px overflow-hidden rounded-md border border-white/10 bg-white/10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {FLOW.map(([number, title, body]) => (
              <article key={number} className="min-h-[150px] bg-[oklch(0.115_0.025_250)] p-4">
                <div className="text-[9px] tracking-[0.16em] text-[var(--color-neon-cyan)]">
                  {number}
                </div>
                <h3 className="mt-5 text-sm font-semibold tracking-[0.04em] text-[var(--foreground)]">
                  {title}
                </h3>
                <p className="mt-2 text-[10px] leading-6 text-[var(--muted-foreground)]">{body}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ── Domains ──────────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            eyebrow="Across the Grid"
            title="One grammar, many applications."
            copy="MoScripts should remain discoverable wherever Grid law is expressed, without tying sovereignty to TypeScript, Python, Cypher, a provider SDK or a single inference generation."
          />

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {DOMAINS.map(([title, body], index) => (
              <article
                key={title}
                className="flex items-start gap-3 rounded-md border border-white/10 bg-white/[0.025] p-4"
              >
                <div className="grid h-9 w-9 flex-none place-items-center rounded-full border border-[var(--color-neon-gold)]/40 bg-[oklch(0.24_0.07_80/0.2)] text-lg neon-text-gold">
                  {GLYPHS[index][0]}
                </div>
                <div className="min-w-0">
                  <strong className="block text-xs font-semibold tracking-[0.06em] text-[var(--foreground)]">
                    {title}
                  </strong>
                  <span className="mt-1 block text-[10px] leading-6 text-[var(--muted-foreground)]">
                    {body}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* ── Security boundary ────────────────────────────────────────── */}
        <section className="grid items-center gap-6 rounded-md border border-[var(--color-neon-orange)]/35 bg-[oklch(0.24_0.08_55/0.16)] p-5 sm:p-6 lg:grid-cols-[160px_1fr]">
          <div className="grid min-h-28 place-items-center border-b border-[var(--color-neon-orange)]/30 pb-4 text-6xl text-[var(--color-neon-orange)] lg:border-r lg:border-b-0 lg:pb-0">
            🜔
          </div>
          <div>
            <div className="text-[10px] tracking-[0.24em] uppercase text-[var(--color-neon-orange)]">
              Security boundary
            </div>
            <h3 className="mt-2 text-lg font-semibold tracking-[0.04em] text-[var(--foreground)]">
              Glyphs express identity. Obscurity does not establish trust.
            </h3>
            <p className="mt-3 text-xs leading-7 text-[var(--muted-foreground)]">
              Symbolic encoding is part of MoScripts&apos; language and cultural form, but it must
              not be treated as encryption.{" "}
              <strong className="text-[var(--foreground)]">
                Authenticity comes from schema validation, stable IDs, deterministic digests,
                signatures, RBAC, provenance, constitutional binding and governed execution.
              </strong>{" "}
              The Grid should remain secure even when every glyph mapping is publicly understood.
            </p>
          </div>
        </section>

        {/* ── Footer ───────────────────────────────────────────────────── */}
        <footer className="flex flex-col justify-between gap-4 border-t border-white/10 pt-6 pb-2 text-[10px] leading-6 text-[var(--muted-foreground)] sm:flex-row">
          <div>
            <strong className="font-medium neon-text-gold">Home of Glyphs</strong>
            <br />
            Law is discoverable. Meaning is registered. Execution is governed.
          </div>
          <div>“Scripts are younger than the symbols that encode them.” · MoStar</div>
        </footer>
      </div>
    </PageShell>
  );
}
