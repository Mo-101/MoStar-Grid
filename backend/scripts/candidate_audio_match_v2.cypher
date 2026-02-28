// ── 1. Candidate match by EXACT Ibibio Word name ─────────────────
// We use a regex or boundary check to avoid "partition" matching "ti"
MATCH (a:AudioSample), (w:IbibioWord)
WHERE a.filename =~ (".*[_\\-]" + toLower(w.word) + "[_\\-\\].].*")
   OR a.filename =~ ("^" + toLower(w.word) + "[_\\-\\.].*")
WITH a, w, "Exact Word Name Match" as strategy, 1.0 as confidence
RETURN a.filename AS audio, w.word AS word, w.english AS meaning, strategy, confidence
ORDER BY audio

UNION

// ── 2. Candidate match by EXACT English Gloss (hyphenated) ───────
MATCH (a:AudioSample), (w:IbibioWord)
WHERE toLower(a.filename) CONTAINS replace(toLower(w.english), ' ', '-')
   AND NOT (toLower(a.filename) CONTAINS 'partition' AND toLower(w.word) = 'ti') // specific case
WITH a, w, "Exact English Gloss Match" as strategy, 0.9 as confidence
RETURN a.filename AS audio, w.word AS word, w.english AS meaning, strategy, confidence
ORDER BY audio;
