// ============================================================
// MoStar Grid — Audio File Mapper
// Sets audio_file on IbibioWord nodes by English meaning match
// Run: cypher-shell < map_audio_to_words.cypher
// ============================================================
// Audio path prefix (relative to Neo4j import dir)
// All paths stored as relative strings for portability

// ── LS100019 series (simple keyword filenames) ────────────────
MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'spoon'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_spoon.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'stunted'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_stunted.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'mouth'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_mouth.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'nose'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_nose.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'neck'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_neck.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'face'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_face.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'stone'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_stone.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'bird'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_bird2.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'burnt' OR toLower(w.english) CONTAINS 'scorched'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_burnt.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'cassava'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_cassava.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'catch sight'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_catchsightof.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'caterpillar'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_caterpillar.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'cigarette'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_cigarette.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'confine'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_confine.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'copulat'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_copulate.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'cough'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_cough.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'cripple'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_cripple.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'cross' AND toLower(w.english) CONTAINS 'over'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_crossover.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'die' OR toLower(w.english) CONTAINS 'perish'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_die.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'ebb'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_ebb.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'follow'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_follow.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'grind'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_grind.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'hang'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_hang.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'knock'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_knock.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'leech'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_leech.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'let fall'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_letfall.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'lift' AND toLower(w.english) CONTAINS 'heavy'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_liftsomethingveryheavy.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'midget' OR (toLower(w.english) CONTAINS 'shorter than normal')
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_midget.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'partition'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_partition.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'polish'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_polish.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'rise' OR toLower(w.english) CONTAINS 'puff' OR toLower(w.english) CONTAINS 'swell'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_rise.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'sweep'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_sweep.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'vomit' OR toLower(w.english) CONTAINS 'retch'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_vomit.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'walk' OR toLower(w.english) CONTAINS 'journey'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100019_ibibio_MU_walk.mp3';

// ── LS100020 series ────────────────────────────────────────────
MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'banana'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_banana.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'cowrie'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_cowrie_shell.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'dirt' OR toLower(w.english) CONTAINS 'refuse' OR toLower(w.english) CONTAINS 'garbage'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_dirt.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'edge' OR toLower(w.english) CONTAINS 'side'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_edge.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'groundnut' OR toLower(w.english) CONTAINS 'peanut'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_peanut.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'piece'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_piece.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'select' OR toLower(w.english) CONTAINS 'choose'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_select.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'slacken' OR toLower(w.english) CONTAINS 'relax'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_slacken.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'sugar cane'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_sugarcane.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'swallow'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_swallow.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'today'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_today.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'weeds' OR toLower(w.english) CONTAINS 'grass'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/LS100020_ibibio_MU_weeds.mp3';

// ── Ibibio16 series ────────────────────────────────────────────
MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'wish' OR toLower(w.english) CONTAINS 'intend'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/Ibibio16_MU_39_wish.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'busy'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/Ibibio16_MU_40_become_busy.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'enter' OR toLower(w.english) CONTAINS 'go into' OR toLower(w.english) CONTAINS 'join'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/Ibibio16_MU_40_enter.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'fall down' OR toLower(w.english) CONTAINS 'fall'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/Ibibio16_MU_40_to_fall_down.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'lose' OR toLower(w.english) CONTAINS 'throw away'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio16_MU_40_to_lose.mp3';

// ── Ibibio17 series ────────────────────────────────────────────
MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'slug'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/Ibibio17_MU_42_slug.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'mother'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio17_MU_43_mother.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'nest'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio17_MU_43_nest.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'uncircumcised'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio17_MU_43_uncircumsized.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'bitter kola'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio17_MU_43_bitterfruit.mp3';

// ── Ibibio18 series ────────────────────────────────────────────
MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'axe'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_44_axe.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'pocket' OR toLower(w.english) CONTAINS 'bag'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_44_pocket.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'stomach'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_44_stomach.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'liver'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_47_liver.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'thin' OR toLower(w.english) CONTAINS 'light in weight'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_49_thin.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'fan' OR toLower(w.english) CONTAINS 'wave'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_50_fan.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'forget'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_50_forget.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'spit'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_50_spit_out.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'torture'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_50_torture_b.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'body' OR toLower(w.english) CONTAINS 'self'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_55_body.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'crazy' OR toLower(w.english) CONTAINS 'mad'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_55_crazyness.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'gonorrhea'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_57_gonorrhea.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'soup' AND toLower(w.english) CONTAINS 'leaf'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_57_soup_leaf.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'tortoise'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio18_MU_57_tortoise.mp3';

// ── ibibio_5_13 series (descriptions in filenames) ─────────────
MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'stand'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_33_stand_b.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'remove from the embers'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_34_remove_from_the_embers_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'sleep'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_34_sleep_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'fierce' OR toLower(w.english) CONTAINS 'brave' OR toLower(w.english) CONTAINS 'dare'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_35_fierce_brave_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'soak' OR toLower(w.english) CONTAINS 'steep' OR toLower(w.english) CONTAINS 'dip'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_35_soak_steep_dip_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'collect' OR toLower(w.english) CONTAINS 'gather'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_36_collect_gather_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'marry'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_38_marry_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'smooth'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_38_become_smooth_b.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'climb'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_38_climb_up_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'send' OR toLower(w.english) CONTAINS 'send for'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_38_send_message_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS "men's robes" OR toLower(w.english) CONTAINS 'mens robes'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_9_mens_robes_b.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'eight'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_eight_a.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'three'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_5_13_MU_three_a.mp3';

// ── Long-description series (Itoro Ituen + Mfon) ───────────────
MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'plead' OR toLower(w.english) CONTAINS 'entreat' OR toLower(w.english) CONTAINS 'beg'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Itoro-Ituen_01Jul2014-1234_plead-plead-with-entreat-beg.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'peel' AND (toLower(w.english) CONTAINS 'knife' OR toLower(w.english) CONTAINS 'unlock')
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Itoro-Ituen_01Jul2014-1258_peel-with-hand-or-knife-as-kola-ndiya-cassava-unlock-bleach.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'call' AND (toLower(w.english) CONTAINS 'read aloud' OR toLower(w.english) CONTAINS 'invite')
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_itoro-ituen_01Jul2014-1435_call-read-aloud-invite.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'hit' AND toLower(w.english) CONTAINS 'beat'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_itoro-ituen_02Jul2014-1550_hit-beat-hollow-or-flat-sounds.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'thing' AND toLower(w.english) CONTAINS 'something'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Itoro-Ituen_03Jul2014-1019_thing-something-matter-event-This-is-one-of-the.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'calabash'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Itoro-Ituen_03Jul2014-1239_a-large-calabash-used-as-a-buoy-for-nets-var-Nkp.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'loosen' OR toLower(w.english) CONTAINS 'untie' OR toLower(w.english) CONTAINS 'dismantle'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_02Jul2014-1651_loosen-untie-unwrap-unfasten-dismantle.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'push' AND toLower(w.english) CONTAINS 'heavy'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-0731_push-a-heavy-object-for-a-distance-shove-away-fro.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'skin scab' OR toLower(w.english) CONTAINS 'natural covering'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-0753_a-natural-covering-skin-scab-var-Nkpa.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'small sticks' AND toLower(w.english) CONTAINS 'yam'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-0800_small-sticks-used-to-support-young-yam-shoots-var.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'regret'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-0805_regret-var-NkpefiOk.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'small' AND w.pos CONTAINS 'adjective'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-0811_small-var-Nkpara.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'prison' OR toLower(w.english) CONTAINS 'jail' OR toLower(w.english) CONTAINS 'detention'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-0942_prison-var-NkpOkOp.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'rough skin' OR toLower(w.english) CONTAINS 'tough skin'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-0947_rough-skin-tough-skin-var-NkpIriikpu-idem.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'seat without a back'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-0959_a-seat-without-a-back-var-Nkpono.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'catch in the hands'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_03Jul2014-1005_catch-in-the-hands.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'remove from a hook' OR toLower(w.english) CONTAINS 'unhang'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_18Sep2014-0728_remove-from-a-hook-unhang-rev-of-k-n-HH.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'ring' AND w.pos CONTAINS 'noun'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_18Sep2014-0732_ring-var-Nkpa-inuen-Nkpa-inuun-Nkpa-nnuun-Nkpa.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'hang an object on a hook'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_18Sep2014-0746_hang-an-object-on-a-hook-around-a-person-8217-s.mp3';

MATCH (w:IbibioWord) WHERE toLower(w.english) CONTAINS 'spread out to dry'
SET w.audio_file = 'data/Ibibio_codex/Ibibio_audio/ibibio_Mfon-Udoinyang_18Sep2014-0747_hang-on-a-hook-peg-line-spread-out-to-dry-ho.mp3';

// ── Verify: count words with audio mapped ─────────────────────
MATCH (w:IbibioWord) WHERE w.audio_file IS NOT NULL AND w.audio_file <> ''
RETURN count(w) AS words_with_audio;
