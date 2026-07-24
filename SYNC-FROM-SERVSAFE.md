# Sync Report: ServSafe Food Manager Source → Kenzie's ServSafe Journey (prototype app)

**Source:** `servsafe-food-manager-source.md` (local copy in this folder — byte-for-byte identical
to Prepline's copy, diffed to confirm)
**Target:** `lessons.json` (5 of 8 topics currently exist) + `index.html`'s embedded `BANK.v1` quiz
array (~450 questions, plainly clustered by topic in lesson order)
**Method:** One sub-agent per existing topic did a field-by-field comparison of `lessons.json`
against the matching source section, plus a targeted grep-and-check pass over the quiz bank. Three
more agents drafted the topics that don't exist here at all yet (Receiving & Storage, HACCP & Active
Managerial Control, Facilities & Equipment), writing in this app's established voice.
**No files have been edited.** This is the report only — same as the Prepline pass, waiting on your
go-ahead.

## Headline finding

Unlike Prepline (which came back essentially clean — same content, already fact-checked), **Kenzie
is a genuinely earlier draft with real drift**, including the exact dishwasher-temperature confusion
that was called out as a high-priority reason for this whole sync. This app also only has 5 of the
8 topics — Receiving & Storage, HACCP & Active Managerial Control, and Facilities & Equipment don't
exist here at all, despite the home screen already labeling one section "Pest Control & **Facilities**"
with no facilities content behind it.

None of this content ships anywhere (per your CLAUDE.md constraint), so there's no urgency from a
release standpoint — but if you're still using this app yourself to study, the two Norovirus-hours
errors and the inverted dishwasher-temperature lesson are the ones most likely to teach you something
actually wrong.

---

## MATCHES (already correct — no action needed)

- **Contamination** — CDC illness stats, BCP types, FAT TOM, danger zone 41–135°F + 4-hour cumulative
  rule, cross-contamination mechanics, refrigerator storage order mnemonic, TCS food list (minus the
  egg wording gap below), Big 6 exclusion pathogens (minus the Norovirus hours below), 9 allergens
  with the 2023 sesame addition, Flow of Food — all correct.
- **Temperature** — all core cook temps, hot/cold holding, two-stage cooling, 4 safe thawing methods,
  reheat-to-165-within-2-hours, thermometer types/calibration — all correct (see conflicts for a
  handful of quiz-only errors).
- **Personal Hygiene** — handwashing technique/steps, full trigger list, glove rules, personal
  cleanliness, PIC responsibilities — all correct apart from the Norovirus timing conflict below.
- **Cleaning & Sanitizing** — cleaning-vs-sanitizing distinction, 3-compartment sink procedure,
  sanitizer ppm ranges and contact times, cleaning schedules, SDS/chemical safety, deep-cleaning
  complex equipment, master cleaning programs — all correct except the dishwasher lesson below.
- **Pest Control & Facilities** — this topic is a genuinely clean pass. Pest biology figures,
  exclusion gap sizes, IPM steps, PCO licensing, garbage management, response sequence, documentation
  retention — every number and claim checked out against the source, in both the lesson content and
  all 18 quiz questions.
- **Trademark** — no real violations. The app studies "for the ServSafe exam" nominatively, and its
  external-links section correctly points to the real servsafe.com as "the official ServSafe site"
  without claiming to issue certification. One phrase (below) is worth a look but isn't urgent.

## CONFLICTS

### Contamination

**1. Eggs' TCS status is stated too narrowly** — `lessons.json`, topic `contamination`, lesson 5
("TCS Foods"), bullets[3]:
- App: *"Eggs: TCS when cracked or in liquid form"*
- Source: *"Eggs: TCS in the shell and when cracked or liquid — except eggs treated or pasteurized
  to eliminate Salmonella"*
- This implies whole eggs in the shell aren't TCS, which is wrong.
- Proposed fix: *"Eggs: TCS in the shell AND when cracked or liquid — the only way out is if they've
  been treated or pasteurized to wipe out Salmonella"*

**2. Norovirus return-to-work window says 48 hours, should be 24** (the anchor issue) —
`lessons.json`, topic `contamination`, lesson 6 ("Big 6 Pathogens"), bullets[0] and the `memory` field:
- App: *"return only after 48 hours completely symptom-free"* / *"Norovirus: 48 hours after ALL
  symptoms end."*
- Source: 24 hours, not 48, in both places.
- Proposed fix: swap "48" → "24" in both the bullet and the memory hook, wording otherwise unchanged.
- This same 48-hour error recurs in the Hygiene topic (below) and twice more in the quiz bank.

**3. Quiz answer key wrong: raw fish vs. raw beef storage order** — `index.html` line 95:
- App: `q("How should raw fish be stored relative to raw beef?",["Above beef","Below beef","Next to
  beef","Never stored together"],1,"Raw fish stored below raw beef based on required cooking
  temperatures.")` — correctIndex 1 ("Below beef")
- This contradicts the app's own storage-order mnemonic ("Really Fine Beef Gets Prepped": RTE → Fish →
  Beef/Pork → Ground → Poultry) — fish belongs ABOVE beef, not below.
- Proposed fix: `q("How should raw fish be stored relative to raw beef?",["Above beef","Below
  beef","Next to beef","Never stored together"],0,"Raw fish goes ABOVE raw beef in the fridge —
  remember 'Really Fine Beef Gets Prepped': Ready-to-Eat, Fish, Beef/Pork, Ground meat, Poultry, top
  to bottom.")`

### Time & Temperature

**1. Dishwasher memory hook conflates water and surface temps** — `lessons.json`, topic
`temperature`, lesson 7, `memory` field:
- App: *"High-temp dishwasher: 180°F at dish surface"*
- Source: *"180°F final-rinse water at the manifold (dish surface reaches ~160°F)"*
- Proposed fix: *"High-temp dishwasher: 180°F final-rinse WATER at the manifold (dish surface itself
  only needs ~160°F — don't mix these up!) / Chemical dishwasher water: 120°F"*

**2. Rabbit misclassified as poultry** — `index.html` line 384:
- App: correctIndex 3 (165°F), explanation *"Rabbit is classified with poultry and must reach 165F."*
- Rabbit is a mammal (game), not poultry — it follows the whole-cuts rule, 145°F.
- Proposed fix: correctIndex 1 (145°F), *"Don't fall for it — rabbit is game, not poultry. It only
  needs 145F like any other whole cut (155F if it's ground)."*

**3. "Commercially raised game animals" wrongly set at 165°F** — `index.html` line 453: same error
pattern as #2 — farm-raised game mammals (venison, bison, etc.) get the standard 145°F whole-cuts
rule, not poultry's 165°F. Proposed fix mirrors #2's correction.

**4. Pork chops tied to the roast "3-minute rest" rule** (lower severity — the temperature itself,
145°F, is correct) — `index.html` line 196: the source separates whole intact cuts (145°F/15 sec, no
rest needed) from roasts (145°F + 3-min rest, because of carryover heat in a large mass). A chop is a
whole cut, not a roast. Proposed fix: drop the rest-time language, note pork chops as a straightforward
145°F/15-second whole-cut item.

**Flagged for a second look, not a confirmed conflict:** `index.html` line 383, a "2-hour/4-hour rule"
question describing a three-tier ladder (0–2 hrs safe / 2–4 hrs use immediately / 4+ hrs discard) that
doesn't match the source's simpler cumulative-4-hour cutoff. The assigned source excerpt doesn't
directly address this phrasing, so it's flagged rather than rewritten blind — worth a look with the
full source doc in hand.

### Personal Hygiene

**1. Norovirus 48-vs-24 hours, recurring** — `lessons.json`, topic `hygiene`, lesson 5, appears in
`bullets[0]`, `why`, and `tip`, all saying 48 hours instead of 24 (same root error as Contamination
lesson 6). Proposed fix: swap 48→24 in all three fields, same wording otherwise. Also appears twice
in the quiz bank:
- `index.html` line 216: correctIndex should flip from 1 ("48 hours") to 0 ("24 hours").
- `index.html` line 489: same fix, correctIndex 1 → 0.

**2. Eating and drinking rules flattened into one** — `index.html` line 131: the quiz treats eating
and drinking as the same rule ("only in designated areas"), but the source (and this app's own
lesson 7) draws a sharp line: drinking is allowed in prep areas ONLY with a covered container and a
straw; eating is never allowed in prep areas regardless of container. Proposed fix: rewrite the
question to test the covered-container-and-straw specifics and note the separate no-eating rule in
the explanation.

**3. Restriction scope narrowed to "ready-to-eat food" only** — `index.html` line 403: restriction
means no food contact and no food-contact-surface contact at all (raw included), not just RTE food.
Proposed fix: broaden the question and explanation to "any food contact or food-contact surfaces."

**4. Trademark phrasing, low priority** — `lessons.json`, hygiene lesson 8: *"ServSafe certification
satisfies this in most jurisdictions"* vs. the source's more generic *"an accredited food protection
manager certification satisfies this."* Not a real violation (nominative, naming what this app studies
for), but if you want to tighten it: *"an accredited food protection manager certification (like
ServSafe) satisfies this in most jurisdictions."*

### Cleaning & Sanitizing

**1. The dishwasher lesson inverts the water-vs-surface facts throughout — the single biggest
finding in this whole sync.** `lessons.json`, topic `cleaning`, lesson 4 ("Commercial Dishwashers"):
the app's `example`, `bullets`, `why`, and `memory` fields all state that the DISH SURFACE must reach
180°F, and invent a "190°F to 194°F" compensating water temperature to explain the gap. The source is
clear: the final-rinse WATER at the manifold must reach 180°F, and because the dish absorbs heat more
slowly, the SURFACE only needs to reach ~160°F. This is exactly backwards from what's currently
written, in the lesson the exam tests hardest.

Proposed replacement lesson (full text, same fields, Kenzie's voice):

> **example:** "HIGH-TEMPERATURE DISHWASHERS: These sanitize using the final hot water rinse. The
> final-rinse WATER measured at the manifold must reach 180°F. Here's the part everyone garbles: the
> dish absorbs heat more slowly than the water rushing past it, so the dish/utensil SURFACE only needs
> to reach 160°F — you verify that with a max-registering thermometer or a heat-sensitive label. These
> machines typically run manifold water at 180°F to 194°F to guarantee that 160°F surface minimum
> actually gets hit.\n\nCHEMICAL SANITIZING DISHWASHERS: These inject chemical sanitizer at lower
> temperatures. The water must be at least 120°F to clean effectively, and the machine automatically
> injects sanitizer at correct concentration. Test the concentration with a test strip at the start of
> service.\n\nWHEN EITHER FAILS: take it out of service immediately and use the 3-compartment sink
> instead."
>
> **bullets:** ["High-temp dishwasher: final-rinse WATER at the manifold must reach 180°F; the
> dish/utensil SURFACE only needs to reach 160°F (verify with a max-registering thermometer or
> heat-sensitive label)", "Chemical dishwasher: water must be 120°F minimum plus correct sanitizer
> concentration", "Test at start of every service period and after any power interruption or
> malfunction", "Machine failure = take out of service immediately; use 3-compartment sink", "After
> drying cycle: air dry only; do not towel dry dishes", "Do not overload racks — items must be
> separated for proper water and chemical contact"]
>
> **why:** "The 180°F/160°F split exists because dishes act as heat sinks — they absorb thermal
> energy and their surface temperature stays lower than the water rushing past them. The machine has
> to deliver final-rinse water of at least 180°F at the manifold so that, even after heat loss to the
> dish, the surface still reaches the 160°F sanitizing minimum."
>
> **memory:** "🧠 DISHWASHER TEMPS: High-temp: 180°F final-rinse WATER at the manifold (DISH SURFACE
> only needs to hit 160°F). Chemical: 120°F water + correct sanitizer. Both: test at start of service.
> If either fails = take out of service immediately."
>
> **tip:** "Do not mix these up. 180°F is the final-rinse WATER temp at the manifold for HIGH-TEMP
> machines — the dish SURFACE only needs to reach 160°F. 120°F is for CHEMICAL machines, where the
> chemical is the sanitizer and 120°F is just the minimum water temp for effective cleaning. This
> exact distinction trips up more students than almost anything else on the exam."

**2. Quiz answer key wrong: lowest-concentration sanitizer** — `index.html` line 505:
- App: correctIndex 1 ("Quaternary ammonium"), claiming quats work at lower concentrations.
- This contradicts the app's own ppm table (chlorine 50–100, iodine 12.5–25, quats 200–400) — iodine
  is actually the lowest, quats the highest.
- Proposed fix: `q("Which sanitizer is effective at the LOWEST ppm concentration?",["Chlorine
  (50-100 ppm)","Quaternary ammonium (200-400 ppm)","Iodine (12.5-25 ppm)","All three need the same
  concentration"],2,"Iodine works at the lowest concentration range of the three chemical sanitizers —
  just 12.5 to 25 ppm, versus 50-100 ppm for chlorine and 200-400 ppm for quats.")`

**3. Gap in quiz coverage:** despite the water-vs-surface distinction being the most-confused fact in
this topic, no existing quiz question actually tests it directly (160°F only ever shows up as a wrong
answer). Suggested new question: `q("A high-temp dishwasher's final-rinse water measured at the
manifold reads 182F. What does the dish/utensil SURFACE actually need to reach to count as
sanitized?",["182F, same as the water","At least 180F","At least 160F","At least 120F"],2,"The
manifold water needs to hit 180F+, but dishes absorb heat slower than water, so the dish surface
itself only needs to reach 160F minimum — verified with a max-registering thermometer or
heat-sensitive label.")`

### Pest Control & Facilities (pests topic)

No conflicts. One non-conflicting observation: `index.html`'s cockroach quiz question cites "over 200
known pathogens," a figure the source doesn't state one way or the other (it only cites "over 100
pathogens" for flies) — not contradicted, just unverifiable against this source, worth an SME glance
if you want a cited number.

---

## ADDITIONS

### Three entire topics are missing from `lessons.json` and the quiz bank

The home screen already has a "Pest Control & **Facilities**" label with no facilities content behind
the second half of that name. Full drafts for all three missing topics — written in Kenzie's
established voice (casual, second-person, dramatic emphasis, 🧠 memory hooks) rather than the source's
more clinical tone — are below, each with a starter quiz set (12–15 questions; explicitly NOT full
parity with the ~90-questions-per-topic depth the other five topics have — scaling these up is a
larger follow-up if you want it).

<details>
<summary><strong>Receiving & Storage (full draft — click to expand in your editor)</strong></summary>

Drafted by the sub-agent covering this domain: 8 lessons (Approved Suppliers; The Receiving
Inspection; Receiving Temperatures; Rejecting a Delivery; Dry Storage; Cold and Frozen Storage;
Storage Order in the Cooler; Date Marking and FIFO), all facts verified against source lines
1056–1248 — fridge storage order, 7-day date marking counting prep day as Day 1, 41°F/45°F receiving
temps, 90-day shellstock tag retention, 50–70°F/50–60% humidity dry storage, 6-inch floor clearance —
plus 15 starter quiz questions. Full JSON and quiz lines are in the agent transcript for this run; say
the word and I'll paste the complete block into `lessons.json` and `index.html` for your review.

</details>

<details>
<summary><strong>HACCP & Active Managerial Control (full draft)</strong></summary>

8 lessons (variance/HACCP-plan triggers; the 7 principles in order; CCP vs. control point; monitoring
and corrective actions; Active Managerial Control and the 5 CDC risk factors; outbreak response;
imminent health hazards; regulatory inspections), verified against source lines 1249–1452 — all 7
HACCP principles correctly ordered, the Big 5 reportable-illness list correctly scoped narrower than
the Big 6 exclusion list (with an explicit note in the memory hook explaining that both are true at
once), the 4-cumulative-hour rule reused correctly for power-outage scenarios — plus 15 starter quiz
questions.

</details>

<details>
<summary><strong>Facilities & Equipment (full draft)</strong></summary>

8 lessons (materials/NSF standards; installation clearances; handwashing sinks; cross-connections and
backflow; water supply; lighting; ventilation; floors/walls/garbage/pest-proofing), verified against
source lines 1453–1627 — 6"/4" clearance rule, 2x-diameter air gap (never under 1"), 50/20/10
foot-candle lighting tiers, coving rationale — plus 15 starter quiz questions. The drafting agent
correctly did NOT duplicate the dishwasher water/surface facts here since that content lives in the
Cleaning & Sanitizing topic already.

</details>

I've kept the full JSON/quiz text out of the main body of this report since it's long (three ~8-lesson
topic blocks plus 45 quiz lines); let me know if you want it inlined here, or written straight into
draft files for you to diff against `lessons.json`, once you've reviewed the conflicts above.

---

## Progress data

Nothing in this pass touched saved progress. This app persists state via a GitHub raw-content fetch
(`lessons.json`, `Logo.png`) plus what looks like JSONBin-backed sync and local UI state (`S.*`) for
scores/history — none of that was read or modified; this report only compared static content files.

## Next step

Two clear priorities if you want me to apply anything:
1. **The two Norovirus 48→24-hour errors** and **the inverted dishwasher lesson** are the highest-value
   fixes — they're the exact class of error this sync was meant to catch, and they'd actively teach you
   something wrong if you're still using this app to study.
2. The three missing topics are a bigger lift (72 new lessons+questions across all three) — let me know
   if you want those written into the files now, staged separately, or left as reference drafts for
   later.

Waiting on your go-ahead before touching `lessons.json` or `index.html`.
