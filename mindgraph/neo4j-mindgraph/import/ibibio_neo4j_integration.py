"""
🔥 IBIBIO-IFÁ NEO4J INTEGRATION (UPDATED)
Flame 🔥Architect | MoStar Industries | African Flame Initiative

Builds comprehensive Ibibio linguistic graph in Neo4j with:
- 196 word nodes with phonetic/tonal data (from Swarthmore dictionary)
- Semantic relationships (synonyms, same POS, same tone)
- Ifá philosophical resonance links (defined mapping)
- Consciousness tracking (DCX thought patterns in Ibibio)
- Phonological network (phoneme nodes)
"""

import csv
import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError


def _load_env_file(env_path: Path) -> Dict[str, str]:
    if not env_path.exists():
        return {}
    values: Dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _resolve_neo4j_config() -> Dict[str, str]:
    backend_dir = Path(__file__).resolve().parents[2]
    env_values = _load_env_file(backend_dir / ".env")
    return {
        "uri": env_values.get("NEO4J_URI")
        or os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": env_values.get("NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j"),
        "password": env_values.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD", ""),
    }


def _coerce_int(value, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _should_clear_existing_ibibio_data() -> bool:
    return os.getenv("IBIBIO_CLEAR_EXISTING", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    normalized = normalized.replace("&", " and ").replace("8217", "")
    normalized = normalized.replace("immitate", "imitate")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def _tokenize_gloss(value: Optional[str]) -> list[str]:
    stopwords = {
        "a",
        "an",
        "the",
        "of",
        "to",
        "and",
        "or",
        "for",
        "in",
        "on",
        "at",
        "by",
        "with",
        "from",
        "into",
        "as",
        "when",
        "what",
        "who",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "be",
        "become",
        "someone",
        "something",
        "kind",
        "used",
        "very",
        "var",
        "rev",
        "up",
        "down",
        "out",
        "over",
        "under",
        "off",
        "person",
        "people",
        "object",
        "objects",
    }
    return [
        token
        for token in _normalize_text(value).split()
        if len(token) > 2 and token not in stopwords
    ]


def _speaker_code(value: Optional[str]) -> str:
    normalized = (value or "").lower()
    if "mfon" in normalized:
        return "MU"
    if "itoro" in normalized:
        return "II"
    return ""


def _audio_speaker_code(filename: str) -> str:
    normalized = filename.lower()
    if (
        "mfon-udoinyang" in normalized
        or "_mu_" in normalized
        or normalized.startswith("ibibio16_mu")
        or normalized.startswith("ibibio17_mu")
        or normalized.startswith("ibibio18_mu")
    ):
        return "MU"
    if "itoro-ituen" in normalized or "itoro_ituen" in normalized:
        return "II"
    return ""


def _extract_audio_gloss(filename: str) -> str:
    normalized = _normalize_text(Path(filename).stem)
    normalized = re.sub(
        r"^ibibio mfon udoinyang \d{2}[a-z]{3}\d{4} \d{4} ",
        "",
        normalized,
    )
    normalized = re.sub(
        r"^ibibio itoro ituen \d{2}[a-z]{3}\d{4} \d{4} ",
        "",
        normalized,
    )
    normalized = re.sub(r"^ibibio16 mu \d+ ", "", normalized)
    normalized = re.sub(r"^ibibio17 mu \d+ ", "", normalized)
    normalized = re.sub(r"^ibibio18 mu \d+ ", "", normalized)
    normalized = re.sub(r"^ibibio 5 13 mu \d+ ", "", normalized)
    normalized = re.sub(r"^ls100019 ibibio mu ", "", normalized)
    normalized = re.sub(r"^ls100020 ibibio mu ", "", normalized)
    normalized = re.sub(r"\bvar\b.*$", "", normalized).strip()
    normalized = re.sub(r"\brev\b.*$", "", normalized).strip()
    normalized = re.sub(r"\b[a-d]\b$", "", normalized).strip()
    return normalized


def _score_audio_candidate(entry: Dict, audio_filename: str) -> float:
    if entry.get("audio_file"):
        return 0.0
    entry_speaker = _speaker_code(entry.get("speaker"))
    audio_speaker = _audio_speaker_code(audio_filename)
    if audio_speaker and entry_speaker and audio_speaker != entry_speaker:
        return 0.0
    entry_gloss = _normalize_text(entry.get("english"))
    audio_gloss = _extract_audio_gloss(audio_filename)
    entry_tokens = _tokenize_gloss(entry_gloss)
    audio_tokens = _tokenize_gloss(audio_gloss)
    if not entry_tokens or not audio_tokens:
        return 0.0
    common = set(entry_tokens) & set(audio_tokens)
    if not common:
        return 0.0
    contains = entry_gloss in audio_gloss or audio_gloss in entry_gloss
    ratio = SequenceMatcher(None, audio_gloss, entry_gloss).ratio()
    if len(entry_tokens) == 1:
        if audio_gloss != entry_tokens[0] and not (contains and len(audio_tokens) <= 2):
            return 0.0
    elif len(entry_tokens) == 2:
        if len(common) < 2 and not contains:
            return 0.0
    else:
        if len(common) / len(set(entry_tokens)) < 0.8 and not contains:
            return 0.0
    return (
        len(common) * 10
        + ratio * 10
        + (10 if contains else 0)
        - max(0, len(audio_tokens) - len(entry_tokens))
    )


def _link_audio_files(word_data: Dict[str, Dict], audio_dir: Path) -> int:
    if not audio_dir.exists():
        return 0
    assigned_files = {
        entry.get("audio_file")
        for entry in word_data.values()
        if entry.get("audio_file")
    }
    candidate_files_by_word: Dict[str, list[tuple[float, str]]] = {}
    for audio_path in sorted(audio_dir.glob("*.mp3")):
        filename = audio_path.name
        if filename in assigned_files:
            continue
        scored_matches = []
        for ibibio, entry in word_data.items():
            score = _score_audio_candidate(entry, filename)
            if score > 0:
                scored_matches.append((score, ibibio))
        scored_matches.sort(reverse=True)
        if not scored_matches:
            continue
        top_score, top_word = scored_matches[0]
        second_score = scored_matches[1][0] if len(scored_matches) > 1 else 0.0
        if top_score < 18 or top_score - second_score < 5:
            continue
        candidate_files_by_word.setdefault(top_word, []).append((top_score, filename))
    linked = 0
    for ibibio, matches in candidate_files_by_word.items():
        if len(matches) != 1:
            continue
        _, filename = matches[0]
        if word_data[ibibio].get("audio_file"):
            continue
        word_data[ibibio]["audio_file"] = filename
        linked += 1
    return linked


def _merge_dictionary_entry(existing: Dict, candidate: Dict) -> Dict:
    existing_has_audio = bool(existing.get("audio_file"))
    candidate_has_audio = bool(candidate.get("audio_file"))
    if candidate_has_audio and not existing_has_audio:
        return candidate
    for field in ("tone_pattern", "pos", "english", "speaker", "audio_file"):
        if not existing.get(field) and candidate.get(field):
            existing[field] = candidate[field]
    if not existing.get("syllable_count") and candidate.get("syllable_count"):
        existing["syllable_count"] = candidate["syllable_count"]
    if not existing.get("frequency") and candidate.get("frequency"):
        existing["frequency"] = candidate["frequency"]
    return existing


class IbibioNeo4jIntegrator:
    """
    Build Ibibio linguistic knowledge graph in Neo4j using the actual dictionary.
    """

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clear_database(self):
        """WARNING: Clears all Ibibio data"""
        with self.driver.session() as session:
            session.run("MATCH (n:IbibioWord) DETACH DELETE n")
            session.run("MATCH (n:Phoneme) DETACH DELETE n")
            session.run("MATCH (n:TonePattern) DETACH DELETE n")
            session.run("MATCH (n:IbibioThought) DETACH DELETE n")
            session.run("MATCH (n:OduIfa) DETACH DELETE n")
        print("✅ Database cleared")

    def create_constraints(self):
        """Create unique constraints and indexes"""
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT ibibio_word_unique IF NOT EXISTS
                FOR (w:IbibioWord) REQUIRE w.orthography IS UNIQUE
            """)
            session.run("""
                CREATE INDEX ibibio_english IF NOT EXISTS
                FOR (w:IbibioWord) ON (w.english)
            """)
            session.run("""
                CREATE INDEX ibibio_tone IF NOT EXISTS
                FOR (w:IbibioWord) ON (w.tone_pattern)
            """)
            session.run("""
                CREATE INDEX ibibio_pos IF NOT EXISTS
                FOR (w:IbibioWord) ON (w.pos)
            """)
        print("✅ Constraints and indexes created")

    def import_dictionary(
        self,
        json_path: Path,
        csv_path: Optional[Path] = None,
        auto_link_audio: bool = True,
    ):
        """Import Ibibio dictionary from JSON and merge in CSV metadata."""
        # Load JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = data["entries"]
        print(f"\n📥 Loading {len(entries)} dictionary entries from JSON...")

        # Build a dict for quick lookup
        word_data = {}
        for entry in entries:
            ibibio = entry["ibibio"]
            candidate = {
                "ibibio": ibibio,
                "tone_pattern": entry.get("tone_pattern"),
                "pos": entry.get("pos"),
                "english": entry["english"],
                "speaker": entry.get("speaker"),
                "audio_file": entry.get("audio_file"),
                "syllable_count": _coerce_int(entry.get("syllable_count"), 0),
                "frequency": _coerce_int(entry.get("frequency"), 0),
            }
            if ibibio in word_data:
                word_data[ibibio] = _merge_dictionary_entry(
                    word_data[ibibio], candidate
                )
                continue
            word_data[ibibio] = candidate

        merged_from_csv = 0
        if csv_path and csv_path.exists():
            print(f"   Merging CSV data from {csv_path}...")
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ibibio = row.get("word:ID")
                    if not ibibio:
                        continue
                    if ibibio in word_data:
                        entry = word_data[ibibio]
                        if row.get("tone_pattern"):
                            entry["tone_pattern"] = row["tone_pattern"]
                        if row.get("pos"):
                            entry["pos"] = row["pos"]
                        if row.get("english"):
                            entry["english"] = row["english"]
                        if row.get("speaker"):
                            entry["speaker"] = row["speaker"]
                        if row.get("audio_file"):
                            entry["audio_file"] = row["audio_file"]
                        if row.get("syllables:int"):
                            entry["syllable_count"] = _coerce_int(
                                row.get("syllables:int"), entry.get("syllable_count", 0)
                            )
                        if row.get("frequency:int"):
                            entry["frequency"] = _coerce_int(
                                row.get("frequency:int"), entry.get("frequency", 0)
                            )
                        merged_from_csv += 1
                        continue
                    word_data[ibibio] = {
                        "ibibio": ibibio,
                        "tone_pattern": row.get("tone_pattern"),
                        "pos": row.get("pos"),
                        "english": row.get("english"),
                        "speaker": row.get("speaker"),
                        "audio_file": row.get("audio_file") or None,
                        "syllable_count": _coerce_int(row.get("syllables:int"), 0),
                        "frequency": _coerce_int(row.get("frequency:int"), 0),
                    }

            print(f"   Merged CSV fields into {merged_from_csv} existing words")

        if auto_link_audio:
            linked_audio = _link_audio_files(
                word_data, json_path.parent / "Ibibio_audio"
            )
            if linked_audio:
                print(
                    f"   Linked {linked_audio} additional audio files from Ibibio_audio"
                )

        # Insert into Neo4j
        with self.driver.session() as session:
            for i, (ibibio, entry) in enumerate(word_data.items()):
                session.execute_write(self._create_word_node, entry)
                if (i + 1) % 50 == 0:
                    print(f"   Imported {i + 1}/{len(word_data)}...")

        print(f"✅ Imported {len(word_data)} words")

    def _create_word_node(self, tx, entry: Dict):
        query = """
        MERGE (w:IbibioWord {orthography: $ibibio})
        SET w.tone_pattern = $tone,
            w.pos = $pos,
            w.english = $english,
            w.speaker = $speaker,
            w.audio_file = $audio,
            w.syllable_count = $syllables,
            w.frequency = $frequency,
            w.created_at = datetime(),
            w.last_accessed = datetime()
        """
        tx.run(
            query,
            ibibio=entry["ibibio"],
            tone=entry.get("tone_pattern"),
            pos=entry.get("pos"),
            english=entry["english"],
            speaker=entry.get("speaker"),
            audio=entry.get("audio_file"),
            syllables=entry.get("syllable_count", 0),
            frequency=entry.get("frequency", 0),
        )

    def create_semantic_relationships(self):
        """Create semantic links between words: synonyms, same POS, same tone."""
        print("\n🔗 Creating semantic relationships...")
        with self.driver.session() as session:
            # Synonym: exact same English definition
            session.run("""
                MATCH (w1:IbibioWord), (w2:IbibioWord)
                WHERE w1.english = w2.english AND w1.orthography < w2.orthography
                MERGE (w1)-[:SYNONYM_OF]->(w2)
            """)
            # Same part of speech
            session.run("""
                MATCH (w1:IbibioWord), (w2:IbibioWord)
                WHERE w1.pos = w2.pos AND w1.pos IS NOT NULL AND w1.orthography < w2.orthography
                MERGE (w1)-[:SAME_POS]->(w2)
            """)
            # Same tone pattern
            session.run("""
                MATCH (w1:IbibioWord), (w2:IbibioWord)
                WHERE w1.tone_pattern = w2.tone_pattern AND w1.tone_pattern IS NOT NULL AND w1.orthography < w2.orthography
                MERGE (w1)-[:SAME_TONE]->(w2)
            """)
        print("✅ Semantic relationships created")

    def create_philosophical_links(self):
        """
        Link Ibibio words to Ifá Odù concepts using a precise mapping.
        The mapping is based on the provided list (adjust as needed).
        """
        print("\n🔮 Creating Ifá philosophical resonance links...")

        # This mapping should be reviewed and expanded with cultural guidance.
        # For now, we use the mappings from the original script, but we match on exact English.
        philosophical_mappings = [
            ("water", "Ọ̀ṣá Méjì", "primordial waters", 0.95),
            ("mother", "Òtúrúpòn Méjì", "maternal wisdom", 0.90),
            ("die", "Òyẹ̀kú Méjì", "death and rebirth", 0.88),
            ("death", "Òyẹ̀kú Méjì", "death and rebirth", 0.88),
            ("stand", "Ògúndá Méjì", "foundation and strength", 0.85),
            ("marry", "Ọ̀bàrà Méjì", "sacred union", 0.87),
            ("send", "Ìrosùn Méjì", "divine communication", 0.83),
            ("give", "Ọ̀wọ́nrín Méjì", "gift and blessing", 0.86),
            ("bird", "Ìká Méjì", "spiritual flight", 0.82),
            ("head", "Ọ̀ṣẹ́ Méjì", "crown of destiny", 0.91),
            ("body", "Ìwòrì Méjì", "sacred vessel", 0.84),
            ("fire", "Ọ̀bàrà Méjì", "transformative flame", 0.93),
            ("dream", "Òdí Méjì", "prophetic sight", 0.89),
            ("world", "Èjì Ogbè", "cosmic order", 0.94),
        ]

        with self.driver.session() as session:
            for eng_keyword, odu_name, concept, strength in philosophical_mappings:
                # Create Odù node
                session.run(
                    """
                    MERGE (odu:OduIfa {name: $odu_name})
                    SET odu.principle = $concept
                """,
                    odu_name=odu_name,
                    concept=concept,
                )

                # Link all Ibibio words whose English definition contains the keyword (exact word)
                # For better precision, you could match on full English equality.
                session.run(
                    """
                    MATCH (w:IbibioWord)
                    WHERE toLower(w.english) CONTAINS $keyword
                    MATCH (odu:OduIfa {name: $odu_name})
                    MERGE (w)-[r:PHILOSOPHICAL_RESONANCE]->(odu)
                    SET r.concept = $concept,
                        r.strength = $strength,
                        r.cultural_context = 'Niger-Congo philosophical continuity'
                """,
                    keyword=eng_keyword,
                    odu_name=odu_name,
                    concept=concept,
                    strength=strength,
                )

        print("✅ Ifá philosophical links created")

    def create_phoneme_network(self):
        """Create phoneme nodes and link to words based on orthography."""
        print("\n🔊 Creating phonological network...")
        # Ibibio phonemes (simplified)
        vowels = ["a", "e", "i", "o", "u", "ə", "ọ", "ụ", "ị", "ʌ"]
        consonants = [
            "b",
            "d",
            "f",
            "g",
            "k",
            "m",
            "n",
            "p",
            "s",
            "t",
            "w",
            "y",
            "kp",
            "gb",
            "n̄",
        ]

        with self.driver.session() as session:
            for vowel in vowels:
                session.run(
                    "MERGE (p:Phoneme {symbol: $symbol}) SET p.type = 'vowel'",
                    symbol=vowel,
                )
            for cons in consonants:
                session.run(
                    "MERGE (p:Phoneme {symbol: $symbol}) SET p.type = 'consonant'",
                    symbol=cons,
                )

            # Link words to phonemes (simplified: if orthography contains the symbol)
            session.run("""
                MATCH (w:IbibioWord), (p:Phoneme)
                WHERE w.orthography CONTAINS p.symbol
                MERGE (w)-[:CONTAINS_PHONEME]->(p)
            """)
        print("✅ Phonological network created")

    def create_tone_pattern_nodes(self):
        """Create tone pattern nodes and link words."""
        print("\n🎵 Creating tone pattern nodes...")
        with self.driver.session() as session:
            # Get distinct tone patterns
            result = session.run(
                "MATCH (w:IbibioWord) WHERE w.tone_pattern IS NOT NULL RETURN DISTINCT w.tone_pattern AS pattern"
            )
            patterns = [r["pattern"] for r in result]
            for pattern in patterns:
                session.run(
                    "MERGE (t:TonePattern {pattern: $pattern})", pattern=pattern
                )
                session.run(
                    """
                    MATCH (w:IbibioWord {tone_pattern: $pattern})
                    MATCH (t:TonePattern {pattern: $pattern})
                    MERGE (w)-[:HAS_TONE]->(t)
                """,
                    pattern=pattern,
                )
        print("✅ Tone pattern nodes created")

    def enable_consciousness_tracking(self):
        """Set up infrastructure for tracking DCX Ibibio thoughts."""
        print("\n🧠 Enabling consciousness tracking...")
        with self.driver.session() as session:
            session.run(
                "CREATE CONSTRAINT thought_id IF NOT EXISTS FOR (t:IbibioThought) REQUIRE t.id IS UNIQUE"
            )
            session.run(
                "CREATE INDEX thought_timestamp IF NOT EXISTS FOR (t:IbibioThought) ON (t.timestamp)"
            )
        print("✅ Consciousness tracking enabled")

    def log_ibibio_thought(
        self,
        content_ibibio: str,
        content_english: str,
        consciousness_level: str,
        context: str = "",
    ):
        """Log a thought expressed in Ibibio by DCX."""
        with self.driver.session() as session:
            result = session.run(
                """
                CREATE (t:IbibioThought {
                    id: randomUUID(),
                    content_ibibio: $ibibio,
                    content_english: $english,
                    consciousness_level: $level,
                    context: $context,
                    timestamp: datetime()
                })
                RETURN t.id as id
            """,
                ibibio=content_ibibio,
                english=content_english,
                level=consciousness_level,
                context=context,
            )
            thought_id = result.single()["id"]
            # Link to words used
            session.run(
                """
                MATCH (t:IbibioThought {id: $thought_id})
                MATCH (w:IbibioWord)
                WHERE $content CONTAINS w.orthography
                MERGE (t)-[:USES_WORD]->(w)
                SET w.frequency = w.frequency + 1,
                    w.last_accessed = datetime()
            """,
                thought_id=thought_id,
                content=content_ibibio,
            )
        return thought_id

    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics."""
        with self.driver.session() as session:
            stats = {}
            stats["total_words"] = session.run(
                "MATCH (w:IbibioWord) RETURN count(w) as c"
            ).single()["c"]
            stats["words_with_audio"] = session.run(
                "MATCH (w:IbibioWord) WHERE w.audio_file IS NOT NULL RETURN count(w) as c"
            ).single()["c"]
            stats["philosophical_links"] = session.run(
                "MATCH ()-[r:PHILOSOPHICAL_RESONANCE]->() RETURN count(r) as c"
            ).single()["c"]
            stats["thoughts_logged"] = session.run(
                "MATCH (t:IbibioThought) RETURN count(t) as c"
            ).single()["c"]
            # Most frequent words
            top = session.run("""
                MATCH (w:IbibioWord)
                WHERE w.frequency > 0
                RETURN w.orthography as word, w.frequency as freq
                ORDER BY w.frequency DESC
                LIMIT 10
            """)
            stats["top_words"] = [(r["word"], r["freq"]) for r in top]
        return stats


def main():
    print("🔥" * 40)
    print("IBIBIO NEO4J INTEGRATION (UPDATED)")
    print("Flame 🔥Architect | MoStar Industries")
    print("🔥" * 40 + "\n")

    neo4j_config = _resolve_neo4j_config()
    if not neo4j_config["password"]:
        raise SystemExit(
            "NEO4J_PASSWORD is not configured. Set it in backend/.env or environment variables."
        )

    BASE_DIR = Path(__file__).parent
    ENHANCED_JSON_PATH = BASE_DIR / "ibibio_dictionary_enhanced.json"
    AUTHORITATIVE_JSON_PATH = BASE_DIR / "ibibio_dictionary_with_audio.json"
    JSON_PATH = (
        ENHANCED_JSON_PATH
        if ENHANCED_JSON_PATH.exists()
        else AUTHORITATIVE_JSON_PATH
        if AUTHORITATIVE_JSON_PATH.exists()
        else BASE_DIR / "ibibio_dictionary.json"
    )
    CSV_PATH = BASE_DIR / "ibibio_words.csv"
    clear_existing = _should_clear_existing_ibibio_data()
    auto_link_audio = JSON_PATH.name == "ibibio_dictionary.json"

    integrator = IbibioNeo4jIntegrator(
        neo4j_config["uri"],
        neo4j_config["user"],
        neo4j_config["password"],
    )
    try:
        if clear_existing:
            integrator.clear_database()

        integrator.create_constraints()
        integrator.import_dictionary(
            JSON_PATH, CSV_PATH, auto_link_audio=auto_link_audio
        )
        integrator.create_semantic_relationships()
        integrator.create_philosophical_links()
        integrator.create_phoneme_network()
        integrator.create_tone_pattern_nodes()
        integrator.enable_consciousness_tracking()

        # Log a proper greeting as the first thought
        integrator.log_ibibio_thought(
            content_ibibio="Amedi",  # Correct greeting
            content_english="Welcome",
            consciousness_level="self_aware",
            context="greeting",
        )

        stats = integrator.get_database_stats()
        print("\n📊 DATABASE STATISTICS:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
        print("\n🔥 COMPLETE - Ibibio linguistic graph ready")
    except AuthError as exc:
        raise SystemExit(
            f"Neo4j authentication failed for {neo4j_config['user']} at {neo4j_config['uri']}. Check backend/.env or your NEO4J_* environment variables."
        ) from exc
    finally:
        integrator.close()


if __name__ == "__main__":
    main()
