# ASD-STE100 Issue 9 — Part 1 Rule Set (extracted)

Extracted from `~/Downloads/ASD-STE100_ISSUE9.pdf` (© ASD 2025, reproduced under stopslop's entity's
licensed usage rights). Source: PDF pages ~43–147 for Part 1; dictionary word list begins PDF page 149.

This file is exempt from the ste100 gate (see `stopslop.config.json`'s own routing rule for this
exact path). It is a dense technical taxonomy of the standard's own rules, not authored prose --
holding it to the standard's own sentence-length and grammar constraints would gut the
cross-references and precision a reference table needs to stay useful.

This replaces the STE100 Gatekeeper System design doc's rule taxonomy (§13.1), which was written
without access to the real spec and is missing/wrong in several places (see `project_scope` memory
for the full list of gaps this corrects).

Checkability legend: **(a)** deterministic, regex/FSM/lookup, no false positives given correct
tokenization; **(b)** heuristic, pattern+context, real error rate; **(c)** genuine semantic/
world-knowledge judgment, not regex-checkable.

---

## Section 1 — Words

**1.1 Which words can you use?** Use words that are approved in the dictionary, OR technical nouns, OR technical verbs. Example: "use" (approved verb), "engine" (technical noun), "ream" (technical verb). — **(a)+(c) mixed**: dictionary-membership lookup is (a); qualifying an out-of-dictionary word as a valid technical noun/verb is (c) (requires the category judgment below). Help: (1) "subject field" = ISO 1087:2019 sense; (2) technical nouns/verbs are usually in your company glossary/terminology database — always check that plus this section's rules.

**1.2 Part of speech.** Use approved words only as their specified part of speech. Example: "test" approved as noun not verb → "Test B is an alternative to test A," not "Test the system for leaks"; "dim" approved adj not verb; "clean" approved as both, disambiguated by sentence position. — **(b)**: needs POS tagging; solid but not error-free. Help: each word's POS is in parens in the dictionary; if a word isn't listed, find its best STE-approved synonym.

**1.3 Approved meaning.** Use approved words only with their approved (often restricted) meaning. Example: "follow" only means "come after/go after," not "obey" — "Follow the safety instructions" is non-STE; must be "Obey the safety instructions." — **(c)**: word-sense disambiguation, not regex-checkable, though a blocklist of the specific commonly-confused words (see 9.2) gives partial heuristic coverage.

**1.4 Forms of verbs and adjectives.** Use only the approved forms given in the dictionary. Verb entries list infinitive/imperative, simple present, simple past, past participle (e.g., REMOVE, REMOVES, REMOVED, REMOVED). Adjective entries list base/comparative/superlative (SLOW, SLOWER, SLOWEST); adjectives taking "more"/"most" have no separate forms listed since those are themselves approved words. — **(a)**: fixed per-entry morphology table, deterministic lookup.

**1.5 Technical nouns — category test.** You can use a word not in the dictionary if it fits one of **22 technical-noun categories** (with non-exhaustive example word lists): 1. Official parts information; 2. Vehicles/machines and locations on them; 3. Tools/support equipment, parts, locations; 4. Materials, consumables, unwanted material; 5. Facilities, infrastructure, logistics; 6. Systems/components/circuits — functions, configs, parts; 7. Mathematical/scientific/engineering terms and formulas; 8. Navigation and geographic terms; 9. Numbers, units of measurement and time (+ symbols); 10. Quoted text; 11. Professional roles, individuals, groups, orgs, geopolitical entities; 12. Parts of the body; 13. Common personal effects, food, beverages; 14. Medical terms; 15. Official documents/parts of documentation, standards, guidelines; 16. Environmental and operational conditions; 17. Colors; 18. Damage terms; 19. Computer science/IT; 20. Civil and military operations; 21. Law and regulations; 22. Animals, plants, other life forms. — **(c)**: category membership is exemplar-based, not exhaustive; requires human/domain judgment. Help: categories give examples only, not a full list; capitalize list words only when necessary (official IDs, titles, abbreviations).

**1.6 Non-dictionary word usable only as technical noun.** A word not approved in the dictionary can be used only if it's a technical noun (or part of one). Worked examples: "base" (not approved, alt = "bottom") is disallowed generically ("at the base of the unit") but fine as a technical noun ("The base of the triangle is 5 cm" — category 7); "backup" (not approved) is fine as technical noun/"backup file" but not as a generic stand-in noun ("available as backup"); "main" (not approved, alt "primary") is disallowed generically but the technical noun "main landing gear" stays as-is even though "primary landing gear" isn't the company's term; "relative" (out of dictionary) is fine inside the technical noun "relative angular position." — **(c)**: same reasoning as 1.5, context-and-company-dependent.

**1.7 Do not use technical nouns as verbs.** Use a technical noun only as a noun/adjective-in-a-noun, never as a verb. Examples: "Oil the steel surfaces" (non-STE) → "Apply oil to the steel surfaces"; "If you think it will snow..." → "If you think that snow will fall..." Also covers words that are legitimately BOTH a technical noun and a technical verb depending on category (e.g., "drill" as noun/tool vs. "drill" as verb/remove-material process). — **(b)**: POS-tagging-based; reliable once a company glossary tags each term's allowed POS, otherwise closer to (c).

**1.8 Use technical nouns approved in your company/industry/subject field.** Example: "touchscreen," "home button." — **(a) conditional**: fully deterministic lookup IF a company terminology database is supplied to the linter; otherwise not checkable at all (external knowledge dependency — a configuration requirement, not a rule the linter can enforce standalone).

**1.9 When you must select a technical noun, use one that's short (≤3 words) and easy to understand.** Example: with illustration+index numbers present, "screws," "flange," "cover" suffice rather than long descriptive noun phrases. — **(a)** for the word-count part (overlaps rule 2.1); **(c)** for "easy to understand."

**1.10 Do not use regional, slang, or jargon words as technical nouns.** Examples: "choker" (regional logging term) → "cable"; "brick" (IT slang) → "set the router to OFF"; "gear" (jargon) → "tools and equipment." — **(c)**: sociolinguistic judgment; a curated slang/jargon blocklist gives partial (b) heuristic coverage but can't catch novel jargon.

**1.11 Do not use different technical nouns for the same item.** Example: non-STE alternates "servo control unit"/"actuator"/"control unit" for one part across three sentences; STE uses "actuator" consistently. — **(b)**: heuristically strong if the document tracks parenthetical index numbers (rule 8.3) — flag when the same index number is referenced by >1 distinct noun phrase; without index numbers, becomes coreference-dependent and closer to (c).

**1.12 Technical verbs — category test.** Same structure as 1.5, for verbs. Four top-level categories, several with lettered subcategories:
1. **Manufacturing processes**: a) Remove material (drill, grind, mill, ream, unsolder); b) Add material (flame, insulate, remetal, retread); c) Attach material (braze, crimp, solder, weld); d) Change mechanical strength/structure/physical properties (anneal, cure, decay, freeze, heat-treat, magnetize, normalize, vaporize); e) Change surface finish (buff, burnish, dress, passivate, plate, polish); f) Change shape (blend, cast, extrude, spin, stamp).
2. **Computer processes and applications**: a) Input/output processes (click, digitize, enter, press, print, swipe, tap, type); b) User interface/application processes (clear, close, copy, cut, delete, deselect, disable, drag, drag and drop, enable, encrypt, erase, filter, highlight, invalidate, maximize, minimize, navigate, open, paste, save, scroll, sort, store, tweet, validate, zoom in, zoom out); c) System operations (abort, boot, communicate, debug, download, format, install, load, manage, process, reboot, update, upgrade, upload).
3. **Instructions/information for applicable subject fields**: a) Engineering/mathematical/scientific (bisect, compensate for, convert, detect, float, modulate, radiate, transform, sink); b) Medical (disinfect, intubate, operate, prescribe, sanitize, sterilize); c) Civil and military operations (aim, arm, detect, disable, dry-motor, enable, explode, fire, inhibit, intercept, lase, load, lock on, unlatch, unload, wet-motor, parachute); d) Navigation (approach, descend, deviate, fly, hover, land, maintain, navigate, retrim, take off, trim, respond, taxi); e) Automotive and railway (accelerate, brake, couple, crank, crash, decouple, dispatch, drift, inflate, park, qualify, steer); f) Energy, oil, and gas (compress, distill, drill, emit, extract, inject, pump).
4. **Law and regulations** (no subcategories): acknowledge, comply with, communicate, conform to, describe, enforce, explain, inform, modify, notify, omit, regulate, sign, supersede, understand, waive.
— **(c)**: same category-membership judgment as 1.5. Help: categories are examples only, not exhaustive; if an approved dictionary verb already gives the instruction accurately, use that instead of reaching for a technical verb.

**1.13 Do not use technical verbs as nouns.** Example: "Give the hole 0.20-inch ream" (non-STE) → "Ream the hole to a 0.20-inch dimension." Past-participle form of a technical verb as an adjective IS allowed ("the reamed hole"). Also covers words that are legitimately both technical noun and technical verb (e.g., "plate" as noun/part vs. verb/manufacturing process). — **(b)**: POS-tagging based.

**1.14 Spelling.** Use American English spelling (per Merriam-Webster) unless other official directives say otherwise; never alter spelling inside quoted text (rule 8.6). Examples: "fibre"→"fiber," "colour"→"color." — **(a)**: British/American spelling-pair lookup table, essentially zero false positives once quoted-text spans are excluded. Help: don't change spelling in quoted text (e.g., on-screen UI text).

---

## Section 2 — Multi-word nouns

**2.1 Write multi-word nouns of no more than three words.** Long noun strings are ambiguous (head noun is usually last; ambiguity worsens for non-native readers whose languages front the head noun). Fix via prepositions. Example: "Runway light connection resistance calibration" (5 words) → "Calibration of the resistance of the runway light connection" (1+1+3 words). — **(b)**: counting is trivial once a noun-phrase chunker correctly identifies phrase boundaries; chunking itself has real error rate.

**2.2 When a technical noun has >3 words, write it in full once, then either (a) give a shorter form, or (b) use hyphens to bind directly-related words into one counted unit.** Method 1: write the long official technical noun in full on first occurrence, then use a defined shorter form or approved abbreviation thereafter (e.g., "ramp service door safety connector pin" → "safety connector pin"). Method 2: hyphenate word groups that function as one unit (e.g., "cutoff-switch power connection" = 3 words). Do not hyphenate everything just to force compliance. Existing official hyphens (e.g., "inward-outward valve") must be preserved as-is. — **(a) for first-use-before-abbreviation tracking** (classic acronym-expansion check, deterministic); **(c) for hyphen-appropriateness judgment**.

---

## Section 3 — Verbs

**3.1 Use only the verb forms given in the dictionary.** — **(a)**: dictionary verb-forms lookup.

**3.2 Use only these forms/tenses: infinitive, imperative (command), simple present, simple past, simple future, past participle (as adjective).** Explicitly bans present perfect (has/have + V-ed), past perfect (had + V-ed), present/past progressive (is/was + V-ing), and all other complex constructions. — **(a)**: auxiliary-verb + participle pattern detection (have/has/had + past-participle; be-form + present-participle) is a small, well-defined, high-precision finite pattern set.

**3.3 Use the past participle form as an adjective.** Permitted (not passive voice) only (a) before a noun, or (b) after a form of "be," "become," or "stay." Must be a dictionary-approved form. Example: "the disassembled unit" (before noun); "the unit is fully disassembled" (after "be"). — **(a)/(b)**: syntactic-position detection is largely deterministic; the specific-word-approved check is a lookup (a).

**3.4 Do not use auxiliary verbs to make complex verb constructions.** Bans "have" + past-participle and modal/be + past-participle passive constructions ("is to be installed," "can be adjusted," "must be adjusted," "will be adjusted"). — **(a)**: same finite auxiliary-pattern set as 3.2.

**3.5 Use the "-ing" form of a verb only as a technical noun or as a modifier in a technical noun.** Only a small closed whitelist of -ing dictionary words exists: nouns (lighting, opening, routing, servicing), adjectives (mating, missing, remaining), pronoun (something), preposition (during). — **(a)**: any "-ing" token is trivially regex-detectable; checking against the ~9-word closed whitelist is deterministic. One of the most cleanly automatable rules in the whole standard. **[Contradicts our prototype finding that -ing checking needs POS tagging — the real rule is actually closed-whitelist-based, not "everything except approved gerund nouns"; re-verify against the prototype's `ING_NOUN_EXCEPTIONS` set once the real whitelist is confirmed against the dictionary.]**

**3.6 Use the active voice; in descriptive writing, passive is permitted only when the agent is unknown.** Test: "by whom/what?" Passive doesn't always name an agent. Four conversion methods given: (1) front the by-phrase agent as subject; (2) convert an infinitive-passive construction to an active verb; (3) use the imperative in procedures; (4) use "you"/"we" as subject when the agent is the reader/company. — **(b)** for passive-voice detection itself; **(c)** for judging whether the "agent is genuinely unknown" exception legitimately applies.

**3.7 Use an approved verb to describe an action, not a noun or other part of speech (avoid nominalizations).** Examples: "The ohmmeter gives an indication of 450 ohms" → "shows 450 ohms"; "Before the removal of the unit..." → "Before you remove the unit..." — **(b)**: light-verb + deverbal-noun constructions form a listable, moderately reliable pattern class; picking the correct fix requires judgment.

---

## Section 4 — Sentences (only 4.1–4.5 exist; **no rule 4.6** — design doc's citation is fabricated)

**4.1 Write short and clear sentences.** In procedures, give direct imperative instructions. In descriptive writing, one topic per sentence, gradual disclosure, no abstraction, be accurate. — **(c)**: clarity/abstraction/one-topic judgments are not mechanically checkable (sentence length itself is separately covered and IS deterministic, see 5.1/6.3).

**4.2 Do not omit words or use contractions.** Don't drop nouns, verbs, subjects, or articles to shorten sentences; don't use contractions. — **(a) for contractions** (closed word/apostrophe-pattern list, zero false positives); **(c) for omitted-word detection** (complicated by imperative sentences legitimately dropping the subject "you" per rule 5.3).

**4.3 Use a vertical list for complex text.** Colon before first item; identify items with dash/bullet/letter/number; capitalize first letter; period at end only if a full sentence; no comma/semicolon at item end; period after last item. — **(a)/(b)**: punctuation-position rules are mechanically checkable; the "full sentence vs. fragment" distinction needs light parsing.

**4.4 Use connecting words and connecting phrases to connect sentences with related topics.** Approved: "and," "but," "then," "thus," "as a result," "at the same time." — **(a) for flagging disallowed connectors** (e.g. "however," "since," "therefore" are explicitly non-STE per the recurring-errors list); **(c) for detecting where a connector is missing/needed**.

**4.5 When applicable, use an article (the/a/an) or demonstrative adjective (this/these) before a noun or multi-word noun.** Don't use articles before general/abstract statements or uncountable concepts. No definite article before a noun immediately followed by an alphanumeric identifier (e.g., "circuit breaker 36L7," not "the circuit breaker 36L7"). — **(c)** overall: article generation/checking is a famously hard NLP problem; **(a) sub-case**: the no-article-before-alphanumeric-ID pattern is cleanly regex-detectable.

---

## Section 5 — Procedural writing

**5.1 Write short sentences. Maximum 20 words per sentence** (procedural sentences AND warnings/cautions/safety instructions; Notes get 25, per 5.5). — **(a)**: fully mechanical word count once Section 8's counting conventions are applied.

**5.2 Write only one instruction per sentence, unless two or more actions occur at the same time.** Exceptions: (a) simultaneous actions, (b) a result occurring immediately after an action. — **(b) for detecting multi-verb sentences**; **(c) for validating the simultaneity/immediate-result exception**.

**5.3 Write instructions in the imperative (command) form.** Do not use "must" before the imperative unless the instruction is safety-critical or states an important condition. — **(a)/(b) for imperative-form detection**; **(c) for judging whether "must" usage is safety-justified**.

**5.4 When there's a condition the reader must know first, start the instruction with a descriptive statement, then a comma, then the command.** Comma placement changes meaning. — **(b) for detecting trailing-conditional pattern**; **(c) for comma-placement-changes-meaning judgment**.

**5.5 Write notes only to give information, not instructions.** Notes must not contain the imperative form, instructions, requirements, or limits/results of a work step. Max 25 words/sentence. Validation method given: read the procedure with notes stripped out — if it becomes incomplete/incomprehensible, the note contains essential info that must be promoted into a numbered work step. — **(a) for imperative-form detection inside NOTE blocks**; **(c) for judging whether informational content is secretly a hidden requirement/limit**.

---

## Section 6 — Descriptive writing

**6.1 Give information gradually.** One subject/idea per sentence; don't front-load. — **(c)**: not mechanically checkable.

**6.2 Use key words and key phrases to give your text a logical structure.** Reuse the *same* key terms across consecutive sentences (don't substitute synonyms). — **(c)** overall (terminology-consistency-across-sentences is NLP-hard), with **(b)** partial coverage via the same consistency-tracking approach as rule 1.11.

**6.3 Write short sentences. Maximum 25 words per sentence.** — **(a)**: identical mechanism to 5.1.

**6.4 Use paragraphs to show related information.** Each paragraph starts with a topic sentence. — **(c)**: paragraph/topic segmentation quality isn't mechanically verifiable.

**6.5 Make sure each paragraph has only one topic.** — **(c)**: same as 6.4.

**6.6 Make sure no paragraph has more than six sentences.** — **(a)**: sentence-per-paragraph counting is trivial and reliable once sentence-boundary detection is in place.

---

## Section 7 — Safety instructions

**Definitions.** Safety instructions tell readers that a procedure/work step can be dangerous or cause damage. **WARNING** = risk of injury or death to persons; **CAUTION** = risk of damage to objects only.

**7.1 Use an applicable word (e.g., "warning" or "caution") to identify the level of risk.** Injury/death risk → WARNING; equipment-damage-only risk → CAUTION; both together → WARNING (higher severity wins). — **This is the most important checkability split in the whole standard for a safety linter to get right**: **(a)** label-presence/format (does every recognized block start with an approved risk-level token) is fully deterministic; **(c)** whether the *correct* severity was chosen for the actual real-world hazard is genuine safety-domain judgment that cannot be derived from the text alone — a linter can enforce that a label exists and is well-formed, but can NEVER verify or guarantee WARNING vs. CAUTION was chosen correctly.

**7.2 Start a safety instruction with a clear and accurate command or condition.** Direct imperative, or condition-first if the reader needs it (mirrors 5.4). — **(a)/(b)**: pattern detection largely deterministic; **(c)** for the "clear and accurate" qualifier (can't verify factual accuracy against real hazards).

**7.3 Give an explanation to show the risk or possible result.** Every safety instruction must state what happens if the reader doesn't obey — never a bare command. — **(b)** for presence-of-a-consequence-clause; **(c)** for whether the stated risk is factually accurate/complete (outside a linter's scope).

---

## Section 8 — Punctuation and word count

**8.1 You can use all standard English punctuation marks but not the semicolon.** — **(a)**: trivial literal-character regex.

**8.2 Use hyphens to connect words that are directly related.** Five sanctioned patterns (multi-word adjectives before a noun; two-word fractions; letter/number + noun showing shape; verb+noun compounds; vowel-adjacency prefixes). — **(b)** overall.

**8.3 You can use parentheses for 7 listed purposes** (illustration refs, index numbers, work-step IDs, abbreviations, singular/plural at once, explanatory asides, alternatives). — **(b)**.

**8.4 In a vertical list, a colon has the same word-count effect as a period, ending a sentence.** — **(a)**: purely mechanical tokenization convention.

**8.5 Text in parentheses counts as one word in the containing sentence.** — **(a)**.

**8.6 Count each of these as one word:** numbers, numbers+units, abbreviations, alphanumeric identifiers, quoted text, titles/headings/placard text, proper nouns of individuals/groups/organizations/geopolitical entities. — **(a)** for numeric/unit/abbreviation/quoted-text/alphanumeric-ID subcases; **(b)** for proper-noun and title/heading detection without explicit markup. Essentially a full tokenizer spec for a word-count function.

**8.7 Hyphenated words count as one word.** — **(a)**: trivial tokenization rule.

---

## Section 9 — Writing practices

**9.1 Use a different sentence construction to write a sentence when a word-for-word replacement is not sufficient.** Four failure modes requiring restructuring: different POS, meaningless literal swap, meaning-changing swap, word absent from dictionary entirely. — **(c)**: fundamentally a semantic/compositional paraphrase task. **This is the clearest rule in the entire standard describing what an LLM-based rewriting step must do, as distinct from what a deterministic linter can flag** — it cannot be regex-checked, only regex-*triggered* (detect a non-approved word, then hand off to semantic rewriting). This is effectively the formal spec for the design doc's "semantic resolver" component, and the design doc never ties its own architecture back to this rule.

**9.2 Use each approved word correctly (respect restricted meanings/POS).** Concrete list of commonly-misused approved words given (wear, extend, go down/through, see, turn, above/below, work, help, damage). — **(c)** overall, but **(b)** heuristic coverage is realistic via a maintained blocklist of exactly these commonly-confused word/POS pairs — probably the single most practically implementable "semantic" rule via a curated pattern list.

**9.3 When you use two words together, do not make phrasal verbs.** A small set of phrasal verbs ARE pre-approved with restricted meanings — only these are allowed. — **(c)** overall, but a maintained blocklist of disallowed phrasal-verb senses gives **(b)** coverage, and the small whitelist of approved phrasal verbs is **(a)**.

**9.4 When you select terminology or wording, always use a consistent style.** Same sentence template and same technical noun for the same part/action across every occurrence. — **(b)**: implementable as a cross-work-step consistency check (same mechanism as rule 1.11).

---

## General Recommendations (GR-1 through GR-8) — advisory, not hard STE rules

**GR-1 The conjunction "that."** Use "that" explicitly after verbs like "make sure," "show," "recommend." — **(b)**: trigger-verb whitelist + parse pattern, moderate false-positive risk.

**GR-2 The preposition "with."** 3 approved meanings, common source of real ambiguity. — **(a)** for flagging every occurrence; **(c)** for judging actual ambiguity.

**GR-3 How to use pronouns.** Only dictionary-approved pronouns (gendered "he"/"she" not approved at all — ties to GR-7). Replace ambiguous pronouns with the actual noun(s). — **(a)** for approved-pronoun-list membership; **(c)** for referent-ambiguity detection, **(b)** heuristic when 2+ plausible antecedents exist nearby.

**GR-4 The pronoun "this."** Make sure the reader knows exactly what "this" refers to. — **(a)** for flagging bare pronominal "this"; **(c)** for the ambiguity judgment.

**GR-5 False friends.** Words that look like a cognate in the writer's native language but mean something different in English. — **(c)**: depends on the writer's native language, not derivable from English text alone.

**GR-6 Latin abbreviations.** Avoid "e.g.," "i.e.," "etc." etc. — **(a)**: closed, finite word list.

**GR-7 Inclusive language** *(new in Issue 9)*. Gendered pronouns not permitted at all; "man"/"woman" not permitted unless necessary. — **(a)** for flagging gendered pronouns and "man"/"woman"; **(c)** for adjudicating the "necessary" exception.

**GR-8 Possessive form** *(new in Issue 9)*. Saxon genitive ('s) permitted but use only when confident it's correct — advisory, not a hard prohibition. — **(a)** for detecting possessive constructions; **(c)** for judging correctness/necessity.

---

## Part 2 (Dictionary) — boundary note

Dictionary word-list body begins at PDF page 149 (internal label 2-1-A1), after ~20 pages of Part 2
front matter. **875 approved words + 1274 non-approved words with alternatives.** Column format:
Col 1 = word + POS (UPPERCASE = approved, lowercase = not approved); Col 2 = approved meaning or
approved alternative(s), sometimes with a Help callout; Col 3 = STE example; Col 4 = non-STE example.

Not yet extracted in full — see [[ste100_prototype]] memory for status. Given stopslop's dictionary
strategy is user-expandable-by-design (base dictionary doesn't cover software vocabulary anyway),
full word-list extraction is lower priority than getting Part 1's rule engine right.
