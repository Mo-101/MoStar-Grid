// ── 1. Candidate match by Ibibio Word name ─────────────────
MATCH (a:AudioSample), (w:IbibioWord)
WHERE toLower(a.filename) CONTAINS toLower(w.word)
WITH a, w, "Word Name Match" as strategy, 1.0 as confidence
RETURN a.filename AS audio, w.word AS word, w.english AS meaning, strategy, confidence
ORDER BY audio

UNION

// ── 2. Candidate match by English Gloss (hyphenated) ───────
MATCH (a:AudioSample), (w:IbibioWord)
WHERE toLower(a.filename) CONTAINS toLower(replace(w.english, ' ', '-'))
   OR toLower(a.filename) CONTAINS toLower(replace(w.english, ', ', '_'))
WITH a, w, "English Gloss Match" as strategy, 0.8 as confidence
RETURN a.filename AS audio, w.word AS word, w.english AS meaning, strategy, confidence
ORDER BY audio;
