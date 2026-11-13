# AUTHOR_WRITING_STYLE.md

A writing-style specification derived from a B.Sc. engineering thesis (Robotics and Mechatronics Engineering, 2024–2026 era): *Design of an IoT-enabled Scalable Closed Hydroponics System with Smart Parameter Control*, 6 chapters plus abstract, acknowledgements and appendix, about 18,000 words of running prose.

---

## A. Activation and scope

**Use this document as the writing-style specification for text you draft or revise in this conversation. Apply the author's recurring stylistic patterns while preserving the requested meaning, factual accuracy, audience, and format. Explicit instructions in the current request take precedence over this guide. The excerpts below are examples to study, not wording to copy.**

What this guide is:

- A description of *how* this author writes: sentence shapes, paragraph moves, how claims, figures, equations, citations and lists are handled, and which habits are absent.
- Usable without the original thesis. Every rule carries a short example or a locator so it can be audited, but you do not need the source to apply it.

What this guide is not:

- It is not a description of the author's identity, opinions or expertise. Do not adopt their topic (hydroponics, IoT, lettuce, XGBoost), conclusions, numbers or institutional context unless the user's task is about those things.
- It is not a source of facts. Nothing here licenses you to add citations, statistics or claims the user has not supplied.
- "The author" below means the writing voice of the manuscript. The thesis has two named candidates and shows signs of more than one drafting hand (see K.3). The guide reproduces the **dominant voice**, and treats a second, more ornate register as a limited, optional layer (C-11).

---

## B. The author's stylistic fingerprint

Ranked from most to least distinctive. Each trait is backed by repeated evidence across chapters, not by a single sentence.

1. **A collective engineering narrator who reports what "we" built, chose and noticed.** The text is written by a team about its own system. *We/our* appear about 13 times per 1,000 words (113 × *we*, 121 × *our*; never *I*). The system is called "our proposed system" (23 times) or "our system", even in the results and conclusion. Narration and procedure alternate: decisions and discoveries are told in the first person ("we noticed", "we learned", "we developed"), while mechanisms and procedures are in the passive ("The probe was immersed…", "The readings are then calibrated…").

2. **Problem → discovery → consequence → decision chains.** The most distinctive move in the methods writing. The author narrates engineering iteration as a short causal story: something was tried, a defect was *noticed*, its cause was *learned*, so the approach changed. Signature connectors are *As we kept running…*, *we noticed that…*, *Upon investigation, we learned that…*, *As such,…*, *This led us to…*, and *This problem was mitigated by…*. Headings mirror this as paired "Initial Approach…" / "Current Approach…" subsections.

3. **Modular, template-driven sections that reuse sentence frames on purpose.** Parallel items (sensors, related works, actuators) get the same paragraph skeleton, often with near-identical sentences: the sensor-introduction sentence appears 7 times, the "sampling rate … 1 Hz or 1 reading per second" sentence 8 times, and the limitation formula "were neither measured nor controlled. If measured and controlled, the growth rate … would have been significantly greater" 4 times. Consistency across parallel units matters more to this author than variety.

4. **Figure-led exposition.** The visual is the anchor of the paragraph. "Figure N shows…" is the most frequent sentence opener in the thesis (38 sentence starts). There are 91 figure references and 29 instances of "as seen in Figure N". Many paragraphs exist only to introduce or explain a figure.

5. **Lists as the main structuring device.** 43 list environments, about 140 items, in about 25,000 source words. Systems, steps, contributions, limitations, observations, objectives and costs all become numbered lists, usually introduced by a colon-ending sentence ("The details of the modules are as follows:"). The items are full sentences and often short paragraphs.

6. **Plainly asserted confidence, hedged mainly on numbers.** Claims about the system's merit are flat and unqualified ("Our model outperforms all previous works…"; "the growth rate … would have been significantly greater"). Hedging is mostly numerical (*approximately*, *around*) or reserved for explaining anomalies (*most likely due to*, *may have caused*). Limitations are collected in one place, at the end of the conclusion, as a list introduced by "leaves room for future improvement".

7. **Definition first, then mechanism, then why it matters.** Background is built like a textbook: define the term, explain the physical or causal mechanism step by step, give the too-high/too-low consequences, and close with a "Therefore, maintaining optimal X is crucial…" sentence. Then the specific component "our proposed system uses" is introduced.

8. **Explicit chapter signposting.** Chapters open with "In this chapter, we discuss…" and close with a recap and a hand-off: "As we have covered…, in the next chapter, we will go over…". This appears at the end of every main chapter.

9. **Concrete quantities and part names everywhere.** Model numbers, dimensions, voltages, settling times, ranges and percentages are given precisely ("a 1.5-inch suction hose", "12V 30A", "settling time of 2 seconds", "63.12%"). Numbers are usually digits, even small counts ("4 different sensors", "3 pins", "2 GMs").

10. **A plain, slightly formulaic register with a narrow connective set.** The prose is formal but not dense. Sentences are mid-length (median about 19 words). Connectives come from a small set (*However*, *Furthermore*, *Additionally*, *Thus*, *Therefore*, *As such*, *Conversely*, *In comparison*). The prose has no rhetorical questions, exclamations, em dashes, *e.g.*, or contractions (one exception), and only six semicolons in the whole thesis.

**How the traits work together.** The thesis reads as a documented build log written up formally. Each section takes the reader through *what the part is → how it works → what we used → where it is shown → what went wrong → what we changed*. The figure carries the detail, and the list carries the structure. The *we*-narrator supplies the causal thread between decisions, and the passive voice describes the hardware. Confidence comes from concreteness (named parts, measured numbers) rather than from argument. Two things would immediately break the voice: removing the *we*-narrator and the figure-anchoring, or making the prose either elegant and varied or hedged and theoretical.

---

## C. Operational writing rules

Format: **Pattern** → **How to reproduce** → **Evidence** → **Confidence** → **Limits**.
Locators: chapter/section, source file and line, and printed page number of the compiled PDF (verified).

### C-1. Use the collective first person for decisions and discoveries, and the passive for procedures and mechanisms

- **Pattern:** *We* chooses, builds, notices, learns, compares and concludes. Equipment and procedures are described in the passive or with the object as subject ("The probe is connected to…", "The data was downloaded…").
- **Reproduce:** For any action a person decided on, write "we + past-tense verb" (*we developed*, *we chose*, *we observed*, *we estimated*). For how a thing operates or how a step was carried out, use the passive or make the device the subject. Refer to the work as "our proposed system", "our system" or "our model". Never use *I*.
- **Evidence:** "Upon investigation, we learned that this pH probe is unsuitable for being immersed indefinitely…" (Ch4 §4.2.4, Chapter4.tex:324, p. 59); "The pH probe was immersed into the three pH buffer solutions." (Chapter4.tex:285, p. 57). Counts: 113 *we*, 121 *our*, 0 *I*; about 318 *be* + participle passives.
- **Confidence:** High.
- **Density depends on section; do not spread *we* evenly.** Measured *we/our/us* per 1,000 words of prose: Background (Ch2) about 7; Related work (Ch3) about 6; Introduction (Ch1) about 18; Methods (Ch4) about 13 overall but about 40 inside iteration passages (see Chapter4.tex:324–326); Results (Ch5) about 24; Conclusion (Ch6) about 48. Background and related work are almost impersonal (the subject is the concept, the device, or "[Name] et al."). The narrator surfaces where the team made or evaluated something.
- **Limits:** The abstract and conclusion also use *we* for claims ("We also added the feature…"). Tense is not fully consistent in the source (proposal-era *will* survives in methods: "The Nano will transmit the signals…", Chapter4.tex:18). Default to past tense for completed work and present tense for how the system operates. Do not copy the *will*/*is*/*was* drift.

### C-2. Narrate iteration as a causal chain, not as a bare outcome

- **Pattern:** Trial → observation → diagnosis → consequence → decision → result, each step a short sentence or clause.
- **Reproduce:** When the user's material includes something that changed (a method, a part, a plan), write it as:
  1. what was used and why ("…which left us with no alternative but to use…");
  2. *As we kept [using/running] X, we noticed that…*;
  3. *Upon investigation, we learned that…*;
  4. *As such, X is unsuitable for…* / *This led us to…*;
  5. the new approach and how it compares ("Compared to X, Y…");
  6. a measured after-state ("After implementing these solutions, … now … in around 14 hours.").

  Use *This problem was mitigated by…* + a numbered list when there were several fixes.
- **Evidence:** pH sensor (Chapter4.tex:281–326, pp. 57–59); EC sensor (Chapter4.tex:474–476, p. 65); chiller: "After running and testing the thermoelectric Peltier cooler for an extended period, we learned that its cooling capacity was insufficient… This led us to procure a refrigerating aquarium cooler." (Chapter4.tex:654, p. 70), then "This problem was mitigated by introducing two design changes in the system:" (Chapter4.tex:658, p. 71); dosing pumps (Chapter4.tex:806–808); BJT switch: "This led us to develop a solution to overcome this problem:" (Chapter4.tex:901, p. 80).
- **Confidence:** High. Six occurrences of "This led us"; five separate iterated subsystems.
- **Limits:** Use it only where there really was an iteration. Do not invent failures to fill the template. In short texts, one chain per section is enough.

### C-3. Give parallel units a shared skeleton and keep it stable

- **Pattern:** Every sensor, every related work and every actuator follows the same internal order, with partly identical sentences.
- **Reproduce:** Decide the skeleton for the first unit, then reuse it for the others. Repeat a functional sentence verbatim when the fact really is the same ("The sampling rate of the X is set at 1 Hz or 1 reading per second."). Vary only the slots.
- **Evidence:** Sensor skeleton (Ch2 §2.2.1–2.2.6 and Ch4 §4.2.4): "Our proposed system uses a/an [part], as seen in Figure N." → working principle → spec sentence. Related-work skeleton (Ch3 §3.1–3.7, pp. 26–39): "[Name] et al. [n] designed and developed an automated IoT-enabled … system to …. Their system monitors:" → list → mechanism paragraph → figure → **Contributions** list → **Limitations** list.
- **Confidence:** High.
- **Limits:** The repetition is deliberate parallelism. It is not an invitation to copy-paste errors: the source twice reuses a sentence with the wrong sensor name (Chapter4.tex:386, 466). Check every slot.

### C-4. Anchor exposition in figures and tables, and introduce each one before it appears

- **Pattern:** A sentence names the figure and says what it shows, the figure follows, then a paragraph explains it. Many paragraphs open with the reference.
- **Reproduce:** Use these openers: *Figure N shows…*, *Figure N illustrates…*, *As seen in Figure N, …*, *From Figure N, the mechanism … will work as follows:*, *Table N below lists/compares…*, *From Table N, it can be seen that…*. Put "as seen in Figure N" at the end of the sentence that introduces a component. Mention *below* or *above* when the float is adjacent ("as seen below in Figure N").
- **Evidence:** "Figure \ref{3D_rightview} shows the right view of the system, where…" (Chapter4.tex:176); "From Table 3.1, it can be seen that there are substantial limitations in all previous works." (Chapter3.tex:355, p. 40). Counts: 91 *Figure* refs, 15 *Table* refs, 29 × "as seen in", 9 × "as shown in".
- **Confidence:** High.
- **Limits:** If the user's format has no figures (an email, a short abstract), drop the anchoring rather than inventing figures. The abstract has no figure references.

### C-5. Structure with numbered lists introduced by a colon sentence

- **Pattern:** Enumerations carry structure: categories, steps, components, contributions, limitations, observations, objectives.
- **Reproduce:** Write a lead-in that ends with a colon ("Hydroponic systems can be classified into two categories:", "The objectives of this project are as follows:", "For instance:"). Use a numbered list unless items are parallel goals; objectives use "To + verb …" bullets. Each item is a complete sentence. Explanatory items run to 2–5 sentences. Definitional items use a bold term and a colon: "**Bagging:** Short for Bootstrap Aggregating, is…".
- **Evidence:** Ch2 §2.1 (Chapter2.tex:11–16); Ch1 Objectives (Chapter1.tex:40–46, p. 4); Ch5 observations list (Chapter5.tex:168–209, pp. 105–107); Ch6 limitations list (Chapter6.tex:41–49, p. 115).
- **Confidence:** High.
- **Limits:** Short inventories (monitored parameters) are bare noun phrases with no full stop ("1. Humidity 2. Air temperature…"). Do not list-ify a short argumentative paragraph that has no enumerable parts.

### C-6. State evaluative claims flatly; hedge numbers and anomalies, not merit

- **Pattern:** Superiority and adequacy claims are stated without hedges. Approximation words attach to quantities. Speculative explanations of unexpected data get "most likely" or "may have".
- **Reproduce:** Write assessments as direct declaratives ("X outperforms…", "This … exhibits the efficacy of…", "…indicating an excellent fit"). Use *approximately* or *around* for measured or estimated values. For an unexplained dip or outlier, write: *This was most likely due to [cause], leading to [effect]. This may have caused [secondary effect]. In contrast, [comparison] remained [state] since [reason].* Do **not** raise the certainty of what the user gives you. Mirror their confidence using these placements.
- **Evidence:** "Our model outperforms all previous works…" (Chapter5.tex:99, p. 100); "There is a marked dip … This was most likely due to the overcast weather… This may have caused some of the leaves to die. In contrast, the mean number of leaves in P1 remained quite stable since…" (Chapter5.tex:206, p. 107). Count: 38 *may/might/could/likely/approximately/around* in about 18k words.
- **Confidence:** High for the placement pattern. The strength of the original claims is a property of that thesis, not a rule to amplify.
- **Limits:** The source sometimes overclaims (counterfactual certainty in Ch3, "putting our system at the forefront" in Ch6). Reproduce the *directness*, not unsupported magnitude (see I-6).
- **Do not under-correct.** When the user's data supports an interpretation, state it in a plain declarative right after the number ("This highlights / exhibits the efficacy of [X] in [doing Y]."). The author never leaves a result uninterpreted, and withholding a supported conclusion out of caution is as off-voice as inflating one.

### C-7. Background: define → mechanism → consequences → "Therefore, maintaining…" → the component used

- **Pattern:** Concept paragraphs move from general definition to physical mechanism. Then come contrasted extremes (*However, excessively high… Conversely, extremely low…*), a *Therefore* sentence about maintaining the optimum, and finally the component or method adopted.
- **Reproduce:** Paragraph 1: "[Concept] plays a crucial role in / has significant implications for [outcome]. It influences/affects [processes]…" Paragraph 2: "However, excessively high [X] can [harm]… Conversely, extremely low [X] can also [harm]… Therefore, maintaining optimal [X] is essential/crucial for…" Paragraph 3: "Our proposed system uses a [component], as seen in Figure N." Mechanism explanations are chains of short causal sentences ("This light passes through… Carbon dioxide molecules … absorb… The remaining light … reaches the detector.").
- **Evidence:** Air temperature (Chapter2.tex:215–219, p. 14); water temperature (Chapter2.tex:247–251); humidity (Chapter2.tex:272–276); NDIR mechanism (Chapter2.tex:297–301, pp. 18–19).
- **Confidence:** High.
- **Limits:** This is the template for *preliminaries/background* only. Results and related work do not use it.

### C-8. Signpost every chapter or major section at both ends

- **Pattern:** Openers announce scope in the first person. Closers recap in the past or present perfect and point forward.
- **Reproduce:** Opener: "In this chapter, we discuss/summarise [scope]. [What is covered] are explained across the various sections of this chapter to [purpose]." Closer: "As we have covered/briefly discussed [X], in the next chapter, we will go over/describe [Y]." Or "In this chapter, we discussed [X]… In the next chapter, we will go over [Y]."
- **Evidence:** Chapter1.tex:48 (p. 4); Chapter2.tex:5, 419; Chapter3.tex:5, 365; Chapter4.tex:7; Chapter5.tex:9, 364. Eight forward hand-offs in total.
- **Confidence:** High.
- **Limits:** Use it only in multi-section documents. A standalone paragraph or abstract has no hand-off.

### C-9. Be concrete: parts, quantities, units, settings

- **Pattern:** Specific names and numbers replace general description, and the spec sentence is a recurring unit.
- **Reproduce:** Prefer "a 12V DC submersible pump" to "a pump". Give a range with its accuracy ("a measurement range of 400 to 5000 PPM with an accuracy of ±50 PPM"), a time with a qualifier ("approximately 10 seconds"), and a percentage to two decimals when computed ("63.12%"). Use digits for counts in technical contexts ("3 pins", "2 GMs", "14 plants"). A spec sentence template: "The [part] has [n] pins: [list]. It has an operating voltage of [range], a [quantity] range of [range] with [accuracy] accuracy and [extra] [cite]."
- **Evidence:** Chapter2.tex:243 (p. 16), 262, 305 (p. 19); Chapter4.tex:1528 (p. 98).
- **Confidence:** High.
- **Limits:** Use only numbers the user supplies or that are verifiably true. Never fabricate specs to fill the template.

### C-10. Define abbreviations in parentheses at (each) first use, and lean on them afterwards

- **Pattern:** "Full Term (ABBR)" with capitalised full terms, re-introduced freely in new chapters or sections. An acronym appendix exists.
- **Reproduce:** Expand an abbreviation on first use in each major section where it reappears. Use the abbreviation thereafter, including as a modifier ("the GM", "the NSCM", "each GM"). Capitalise the words of the expanded term when they name a system or module ("Growth Module (GM)").
- **Evidence:** "Nutrient Film Technique (NFT)" (Chapter2.tex:20); "Growth Modules(GMs)" (Chapter4.tex:16); "Comma-Separated Value (CSV)" defined twice (Chapter4.tex:979, 1228).
- **Confidence:** High.
- **Limits:** The source often omits the space before the parenthesis ("conductivity(EC)"). That is a typing error. Always put a space before "(" (see I-4).

### C-11. Optional elevated register, kept to framing paragraphs only

- **Pattern:** Two places use a markedly more ornate, promotional vocabulary: the ML background (Ch2 §2.3) and the opening and scaling paragraphs of the Conclusion (Ch6). Words include *pivotal, amalgamates, endeavors, garnered immense popularity, accentuated, propels, realm, usher in a transformative era, grappling, underscores, Intriguingly, tangible demonstration, strategically crafted*. A keyword count over 30 such words gives 15 hits in Ch2 (13 of them in §2.3), 13 in Ch6, 5 in Ch4, 2 in Ch5, 1 in Ch1 and 0 in Ch3.
- **Reproduce:** By default, **don't**. If the user asks for a visionary closing paragraph or a "significance/impact" passage, you may raise the register for that paragraph only. Use at most one or two elevated words per paragraph and keep the sentence shapes of the main voice. Never use this register in methods, results or related work.
- **Evidence:** "Our system holds the potential to usher in a transformative era in agriculture, particularly in regions grappling with an escalating demand for food amidst…" (Chapter6.tex:6, p. 113), set against the plain voice in the next paragraph block: "We tested our system by growing 14 Green Leaf lettuce plants in it. Our lettuce grew much faster…" (Chapter6.tex:16, p. 113).
- **Confidence:** Medium that this is a distinct layer. Low on who wrote it (see K.3).
- **Limits:** This is not the fingerprint. Overusing it is the fastest way to make text sound unlike the dominant author.

### C-12. Close sections on the consequence or implication, often with *Thus* / *This* + verb

- **Pattern:** A paragraph's last sentence draws the practical consequence of the facts before it, usually beginning *Thus,*, *Therefore,*, *This allows/causes/results in/led us to…*, or *This highlights how…*.
- **Reproduce:** End technical paragraphs with what the preceding mechanism *enables* or *causes* for the system or the reader. Do not end on a citation or a bare fact.
- **Evidence:** "This effectively eliminates the need for pesticides. This makes produce from such systems much safer and healthier to consume." (Chapter2.tex:18); "Thus, this equation was used by the Arduino Nano to calculate the pH from the voltage produced at the electrodes." (Chapter4.tex:316, p. 59); "Thus, the imbalanced nature of our dataset can be seen as a testament to the stable environment being maintained by the system." (Chapter5.tex:108, p. 101).
- **Confidence:** High.
- **Limits:** The author often chains two or three *This*-subject sentences in a row. Keep it to at most two, and make each *This* have a clear antecedent.

---

## D. Sentence and paragraph patterns

### D.1 Sentence statistics (for calibration, not targets)

Method: a script stripped the included chapters and the abstract of LaTeX comments, figure, table and equation environments, display math and commands. Inline math became a single token and `\cite`/`\ref` became tokens. Text was split into paragraphs on blank lines (list items counted separately) and into sentences on `. ? !` before a capital or digit, protecting *et al.*, *i.e.* and *Fig.* This is **whole-document coverage** of the included prose (about 895 sentences, about 18,100 words) with approximate segmentation.

| Feature | Value |
|---|---|
| Sentence length, median / mean | about 19 / about 20 words (chapter medians 17–24; Ch3 shortest, Ch1 longest) |
| 90th percentile / max | about 32 / 56 words |
| Distribution | 44% of sentences are 10–19 words, 31% are 20–29, 12% are 30–39, under 4% are 40 or more, 8% are under 10 (mostly list items and lead-ins) |
| Body paragraphs (lists removed) | median 2 sentences, about 51 words; 90th percentile about 92 words; about a quarter are one-sentence paragraphs (mostly figure intros and colon lead-ins to lists) |
| Abstract | one paragraph, 11 sentences, median 20 words |
| Semicolons / em dashes / questions / exclamations | 6 / 0 / 0 / 0 |
| Parentheses | about 98 (mostly abbreviations, units, *i.e.* lists, "(left)/(right)") |
| *i.e.* / *e.g.* | 6 / 0 (the author writes *such as*) |

Implication: write mid-length sentences, 15–25 words, with one or two clauses. Insert an occasional 30–40-word sentence when listing parameters or tracing a mechanism. Keep paragraphs short (two to four sentences). Use one-sentence paragraphs freely when they introduce a figure or a list.

### D.2 Sentence schematics

Use these as shapes, not text. Rotate them. No single schematic should account for most sentences in a section.

1. **Introduce-and-anchor:** `Our proposed [system/approach] uses a/an [named component], as seen in Figure N.`
   *Fits:* the first mention of any concrete component, tool or dataset.
2. **Figure-subject:** `Figure N shows/illustrates [what], [where/which-clause adding a detail].`
   *Fits:* opening a paragraph that explains a visual.
3. **Discovery:** `As we kept [running/testing] [X], we noticed that [symptom], even when [condition].`
   Followed by: `Upon investigation, we learned that [cause].`
4. **Consequence/decision:** `As such, [X] is unsuitable for [purpose], which would require [condition]. This led us to [new action].`
5. **Comparison after a change:** `Compared to [old], [new] could [benefit] and only required [lower cost/effort].`
6. **Too-much/too-little pair:** `However, excessively high [X] can [harm], [participle clause]. Conversely, extremely low [X] can also [harm] by [mechanism].`
7. **Maintenance conclusion:** `Therefore, maintaining [optimal X] is [essential/crucial] for [outcome].`
8. **Prior-work summary:** `[Surname] et al. [n] designed and developed [a system/method] to [goal]. Their system [monitors/controls/uses]:` + list.
9. **Formula limitation:** `[Parameters] were neither [measured] nor [controlled]. If [measured and controlled], [outcome] would have been [significantly greater].`
   *Use sparingly and only with the user's own claim strength.*
10. **Equation lead-in:** `[Quantity] is given by Equation N:` / `The equation for [X] is determined to be:` / `This also brings [Total] to:`
11. **Variable gloss after an equation:** `[symbol] is the [meaning] in [unit], and [symbol] is the [meaning].`
12. **Fit/quality + use:** `Equation N has [a metric of value], indicating [an excellent fit]. Thus, this equation was used by [agent] to [purpose].`
13. **Anomaly explanation:** `There is a marked [dip/rise] in [quantity] between [range]. This was most likely due to [cause], leading to [effect].`
14. **Interpretive claim:** `This [result] exhibits/highlights [the efficacy/advantage] of [our approach] in [doing X].`
15. **Colon lead-in to a list:** `The details of the [modules/steps] are as follows:` / `[Thing] comprises [n] [parts]:` / `For instance:`

Characteristic **openers** (in measured order of frequency): *Figure N…*, *A/An [noun]…*, *Our proposed…*, *If…*, *These…*, *The system…*, *To…*, *Furthermore,…*, *However,…*, *It is…*, *They…*, *Thus,…*, *This led…*, *Due to…*, *Additionally,…*, *Therefore,…*, *As such,…*.

Characteristic **endings**: a citation placed before the full stop, an "as seen in Figure N" clause, a purpose clause (*…to ensure…*, *…such that…*), or a consequence participle (*…, leading to…*, *…, indicating…*, *…, ensuring…*).

### D.3 Paragraph blueprints

**P1. Background concept (preliminaries).** 3 paragraphs.
(a) Importance claim + processes affected + cited general finding. (b) *However* (too high) / *Conversely* (too low) / *Therefore, maintaining…*. (c) "Our proposed system uses…, as seen in Figure N." + one figure.
→ Grounded in Ch2 §2.2.4 (pp. 14–16).

**P2. Component working principle.** 3–4 short paragraphs.
Core parts (*At its core, the sensor employs…*) → step-by-step causal chain (*The process begins with… This light passes through… The detector then measures…*) → advantage + how it is achieved (*One of the key advantages… This is achieved by…*) → spec sentence with citation.
→ Ch2 §2.2.6 (pp. 18–19).

**P3. Prior-work module.** "[Name] et al. [n] designed and developed… to [goal]. Their system monitors:" → noun-phrase list → 1–2 sentences on how it works ("They used… which… The gateway… communicates…") → borrowed figure with citation → **Contributions** (numbered, full sentences, evaluative) → **Limitations** (numbered, often what was *not* measured or controlled plus the consequence).
→ Ch3 §3.1–3.7.

**P4. Iteration subsection (paired headings).** *Initial Approach of X*: why it was chosen (constraint), how it was set up or calibrated (numbered steps), the fitted result. *Current Approach of Using Y*: discovery chain (C-2), "Y also has a more straightforward [process]:" + numbered steps, verification sentence ("To check whether…, … gave a reading of… This indicated that…"), placement sentence with a figure.
→ Ch4 §4.2.4 (pp. 57–65).

**P5. Procedure.** Lead-in with purpose ("…using the following steps:") → numbered steps in a mix of *we* (actions) and passive (operations), each step 1–3 sentences with quantities → a closing paragraph restating the dataset or outcome.
→ Chapter4.tex:400–412 (p. 62).

**P6. Results observation block.** "Figure N shows [what was plotted]…" → *Observations…* heading → numbered list: each item states the observation with numbers, then an interpretation sentence ("This rapid growth … exhibits the efficacy of…"), with anomalies explained by *most likely*.
→ Ch5 §5.2 (pp. 102–107).

**P7. Model or economic derivation.** Define the measure in words ("A suitable measure for… would be…, which we will refer to as…") → word equation → decomposition ("…can be broken down into two sections, as seen in Equation N.") → bold-term definitions list → successive equations, each with a one-line lead-in ("Since the system can be scaled, if we…, then the equation… stands at:") → plots list → plain-language conclusion with the decision threshold ("…can be considered when… falls below…").
→ Ch5 §5.3 (pp. 108–112).

**P8. Conclusion.** Capability recap in the present ("Our system is now fully capable of…") → experiment recap in the past with a headline number → model and scaling recap → wider implication → "However, with all scientific studies, our system too leaves room for future improvement. For instance:" + numbered limitations, each with cause and planned remedy → final forward-looking paragraph on application and the need for interdisciplinary work.
→ Ch6 (pp. 113–116).

---

## E. Vocabulary, transitions and phrasing

### E.1 Transferable preferences (use these)

| Function | Preferred forms (measured counts where useful) |
|---|---|
| Adding | *Furthermore,* (10), *Additionally,* (5), *In addition,*, *also* (very frequent mid-sentence: "is also developed", "We also added") |
| Contrast | *However,* (9, almost always sentence-initial), *Conversely,* (2, for opposite extremes), *In comparison,*, *In contrast,*, *On the other hand,* |
| Consequence | *Thus* (7), *Therefore,* (5), *As such,* (3), *This led us to* (6), *This allows/causes/results in*, *consequently* |
| Exemplifying | *such as* (never *e.g.*), *(i.e., …)* for an enumerating gloss in parentheses, *For instance:* before a list |
| Purpose/manner | *such that* (10), *so that*, *to ensure that*, *per the [requirement/needs]* (9), *per user requirement* |
| Reference | *as seen in Figure N* (29), *as shown in* (9), *as mentioned in*, *the aforementioned*, *the latter*, *said [valve]* |
| Sequencing | *Secondly,*, *Lastly,*, *Upon [noun/gerund],*, *After [gerund],*, *Once [clause],* |
| Process verbs | *monitor*, *control*, *measure*, *maintain*, *regulate*, *actuate*, *mitigate*, *ensure*, *determine*, *implement*, *develop*, *design and develop/build*, *procure*, *accommodate* |
| Evaluation | *optimal* (45), *significant(ly)* (24), *crucial*, *imperative* ("it is imperative to…"), *considerable/considerably*, *substantial*, *marked* ("a marked increase/dip"), *adequate*, *ideal* |

Recurring idiomatic frames that are reusable on any topic:

- "This form of [practice] removes the traditional dependence on [constraint]…"
- "…which left us with no alternative but to…"
- "…appeared redundant to us since…" (justifying a decision not to do something)
- "Not to mention, …" (once; for an additive point in an introduction)
- "To keep [the table] clean, …" (an explicit note on a presentation choice)
- "Apart from [main benefit], our [system] also aims to…"
- "Realistically, …" (to introduce a sober estimate after a model)

### E.2 Subject-specific (do not import unless the topic requires it)

*Growth parameters, nutrient solution, GM/NSCM, actuators, dosing system, DAT, sampling rate of 1 Hz, Arduino Nano/Mega, Raspberry Pi, ThingSpeak, XGBoost, lettuce, CEA, break-even in Taka.* These are content, not style.

### E.3 Avoid (conflicts with the observed voice)

- First-person singular; second person addressed to the reader (*you*); rhetorical questions; exclamation marks.
- Em dashes and en-dash asides. Use commas, parentheses, or a new sentence.
- *e.g.* (use *such as*); *etc.* (not used; the author lists fully or ends with "among others").
- Contractions (one *it's* occurs once, in a conclusion paragraph; treat it as a slip).
- Stacked hedges (*it could perhaps be argued that…*), meta-commentary on uncertainty, or theory-laden framing (*we theorize*, *this problematizes*).
- Literary variation for its own sake: synonym-cycling where the author would repeat the same term (*the GM… the GM… the GM*).
- Semicolon-joined sentences (6 in the whole thesis), dense nominalisation chains, or very long periodic sentences.
- Elevated buzzwords (*pivotal, realm, tapestry, delve, underscore, showcase, transformative*) outside C-11's narrow allowance. Note: *delve(s)* appears 3 times in the source ("where we delve deep into the intricacies of our methodology"). It is part of the elevated layer and must not be used as a default.

---

## F. Section-specific guidance

Only genres present in the source are covered. For other genres, apply sections C and D and use judgement.

| Section | What to do |
|---|---|
| **Abstract** (p. ii) | One paragraph, about 10–12 sentences, no citations, no figure references. Order: broad problem (1–2 sentences) → "As such, [approach] is…" → "Our proposed system seeks to build upon previous works in… and implement…" → current capability ("At this point, our system can…") → added features ("We also added…") → experiment with exact counts → result with exact metric values → secondary demonstrations ("The system's scalability was also demonstrated, along with…"). Mixed tense is acceptable: present for capability, past for experiments. |
| **Introduction** (pp. 1–4) | Open with a large-scale stake supported by statistics and a citation at the end of the stake sentence. Define the field in one plain sentence ("[Field] is [definition]."). Subsections *Problem Definition* → *Motivation* → *Objectives*. Problem paragraphs state a gap observed by "us" ("However, after going through the existing literature…, we observed limitations… as none consider…") and its consequence. Motivation names what is missing and what "our proposed idea is to create". Objectives are "To + verb…" bullets. Close with the chapter recap and hand-off. |
| **Background / Preliminaries** (pp. 5–25) | Textbook register with a citation on nearly every factual sentence. Blueprints P1 and P2. Classifications as numbered lists. Close with "As we have covered some common ground related to…, in the next chapter, we will go over…". |
| **Related work** (pp. 26–41) | Short chapter intro on how the works were selected ("This chapter highlights some of the best works we came across during our literature review. Despite finding a large number…, very few…"). One module per work (P3). End with a synthesis section: restate the full parameter set → "None of the works discussed has…" → comparison table with "our proposed system" as the highlighted last row → "From Table N, it can be seen that…" → additional gaps as paragraphs opening *Furthermore*, *Additionally*, *Lastly* → "Our proposed system is designed to address these limitations… and build upon their strengths". Criticism is factual (what was missing) plus consequence, never personal or rhetorical. |
| **Methodology** (pp. 42–98) | Chronological build narrative: design (CAD) → physical structure → sensors → actuators → electronics → controllers → software/IoT → algorithms → full setup → experimental design → model → extension. Each unit is figure-anchored (C-4). Use the paired Initial/Current subsections for anything that changed (P4). Procedures follow P5. Experimental design opens: "In order to thoroughly evaluate the performance of [X], we designed an experiment:" + design description + treatments as a labelled list ("P1: …"). Measurement definitions are list items with a bold or plain lead term and a colon. |
| **Results** (pp. 99–112) | One-line chapter scope statement. "Figure N shows…" for every plot. Comparison tables with prior work. Interpretations follow the data immediately in the same paragraph. Anomalies get *most likely due to*. Observations go in a numbered list. Economic or model derivations follow P7. Close with a recap and hand-off ("We went over the results we obtained from… In the succeeding chapter, we will go over…"). |
| **Conclusion** (pp. 113–116) | Blueprint P8. Present-tense capability statements, past-tense experiment recap with the key number, then impact. Limitations as a list with remedies in progress ("We have consulted… who will be guiding us…"). Final paragraph: practical deployment + call for interdisciplinary effort. This is the only section where C-11's elevated register may surface, and only in moderation. |
| **Acknowledgements** (p. iii) | Effusive and formal: "We would like to express our heartfelt gratitude to…", "We also deeply thank…", "On a similar note, we offer our sincerest thanks to…". Each person gets their title, affiliation and a sentence on how they helped. The source repeats *unwavering* three times; vary the adjectives. |
| **Captions** | A noun phrase, no final full stop, bold in source, citation at the end for borrowed images. Composite images are described positionally: "…(left) and … (right)". Captions are descriptive, not interpretive ("Loss curve for our model"; "Top view of the sensor board"). |

---

## G. Technical and formatting conventions

### G.1 Likely authorial habits (reproduce when writing LaTeX or structured technical text)

- **Equations** are always introduced by a lead-in sentence ending in a colon, and named in text as "Equation N" (capital E, often "the Equation N"). After the display, a gloss sentence **begins with the symbol**: "$\mathrm{y}$ is the pH of the solution, and $\mathrm{x}$ is the voltage…" (Chapter4.tex:316). Fit or quality and use follow (C-12).
- **Word equations** are preferred for derived measures: `Average Cost = Total Cost (TC) of the System / Total Quantity of Lettuce Produced` (Chapter5.tex:223). Abbreviations are introduced inside the equation text. Variables are set upright with `\mathrm{}`, including chemical formulas (`$\mathrm{CO_{2}}$`, 60+ uses).
- **Formal set notation** appears only briefly and is glossed in plain words immediately: "is a row vector that contains the input variables, i.e., sensor data (or features)" (Chapter4.tex:1232, p. 93).
- **Metric formulas** sit inside list items: "**Precision:** It is the proportion of… It is calculated using the formula:" + display.
- **Citations**: numeric IEEE style in square brackets. They are placed **at the end of the sentence or clause, before the full stop**. Multiple sources are cited as separate brackets "[25], [26], [27]" rather than a range. Citations act as nouns ("Some works, such as [13], have designed…") and as subjects with *et al.* ("D'Anna et al. [69] designed…"). They also appear in section titles of summarised works and inside captions of borrowed figures. Datasheets and vendor pages are cited for component specs.
- **Prior work** is introduced with "designed and developed" or "designed and built" + purpose, never with evaluative reporting verbs (*argue*, *claim*, *suggest*). Disagreement is expressed only as missing coverage plus consequence. Positioning statements: "None of the works discussed has…", "Our proposed system is designed to address these limitations… and build upon their strengths…", "…inspired by [n]".
- **Lists**: numbered (`enumerate`) for almost everything; bullets for objectives and the declaration. Labelled conditions use a code and colon ("P1: Our automated system").
- **Units and numbers**: digits for counts; units attached or spaced inconsistently in the source ("12V", "5 x 2L", "1,400 cm²", "1 Hz"). In new text, use a consistent spaced form ("12 V") unless matching an existing document. Thousands are separated by commas ("57,638"). Percentages are computed to two decimals.
- **Emphasis**: bold for defined terms at the head of list items. Quotation marks for informal or quoted terms ("film", "daylight", "ON"/"OFF" states). No italics for emphasis.
- **Headings**: descriptive noun phrases in Title Case, often long and specific ("Initial Approach of Calibration and Placement of a Low-end pH Sensor"). Related-work section titles reproduce the cited paper's title.
- **Tables** have a lead-in sentence ("Table N shows/lists/compares…") and booktabs-style or fully ruled grids. The proposed system's row is highlighted in comparisons.

### G.2 Template or class-imposed (do not treat as style)

- Thesis class (`Thesis.cls`, derived from the ECS thesis template by Steve Gunn): title page, Declaration of Authorship wording, roman/arabic page numbering, running headers ("Chapter N. *Title*"), caption font, list-of-figures/tables, chapter heading design.
- Bibliography format (IEEEtran.bst) and acronym-appendix layout.
- `[H]` float placement and `\clearpage` pagination are layout choices, not prose style.

---

## H. Worked transformations

All examples below are **newly written demonstrations**, not quotations. Topics were chosen to be unrelated to the source. Meaning and certainty are preserved, and all facts are invented for illustration.

### H.1 Background concept (topic: battery temperature in e-scooters)

**Generic:**
> Temperature is important for lithium-ion batteries. If it gets too hot or too cold, the battery performs worse and ages faster, so it should be kept in a good range. We used a thermistor to measure it.

**In the author's style:**
> Temperature plays a crucial role in the performance and lifespan of lithium-ion batteries. It affects the rate of the chemical reactions within the cells, the internal resistance of the battery, and the amount of charge that can be delivered at a given time.
>
> However, excessively high temperatures can accelerate the degradation of the electrodes, shortening the usable life of the battery. Conversely, extremely low temperatures can also reduce performance by increasing the internal resistance of the cells. Therefore, maintaining an optimal battery temperature is essential for ensuring both the range and the longevity of the scooter.
>
> Our proposed system uses an NTC thermistor to measure the battery temperature, as seen in Figure 2.4.

**Changes made:** split into the three-paragraph P1 blueprint; opened with "plays a crucial role in"; listed affected processes concretely; used the *However… Conversely… Therefore, maintaining…* pair; moved the component into its own anchored sentence with "Our proposed system uses…, as seen in Figure N". The certainty is unchanged ("can", as in the original's "performs worse"). No citations were added, because none were supplied. With sources, they would go before each full stop.

### H.2 Prior-work summary (topic: smart parking)

**Generic:**
> Lee and colleagues made a parking system that uses cameras to find free spots and shows them in an app. It works well but only covers one lot and doesn't handle bad weather.

**In the author's style:**
> Lee et al. [12] designed and developed a camera-based parking guidance system to reduce the time drivers spend searching for vacant spaces. Their system detects:
>
> 1. Occupied spaces
> 2. Vacant spaces
> 3. Vehicles entering and leaving the lot
>
> The camera feed is processed on a local server, which updates the availability of each space on a mobile application.
>
> **Contributions**
> 1. The mobile application provides drivers with real-time information about vacant spaces before they enter the lot.
>
> **Limitations**
> 1. The system was tested in a single parking lot, which leaves its performance across different layouts unverified.
> 2. The detection accuracy under rain and low light was neither measured nor reported.

**Changes made:** "et al. [n] designed and developed … to [purpose]"; "Their system detects:" with a bare noun-phrase list; a mechanism sentence in the passive; a Contributions/Limitations split with full-sentence items; the limitation framed as missing coverage plus consequence. The original's "doesn't handle bad weather" was a claim about untested conditions, so it was rendered as "neither measured nor reported" rather than strengthened into a counterfactual.

### H.3 Iteration narrative (topic: a sensor mount on a weather station)

**Generic:**
> We first glued the wind sensor to the mast, but the glue failed in the sun after a few days, so we switched to steel clamps, which work fine.

**In the author's style:**
> The anemometer was initially mounted to the mast using an epoxy adhesive. After running the weather station outdoors for an extended period, we noticed that the anemometer had begun to tilt away from the vertical. Upon investigation, we learned that the adhesive softened under direct sunlight, which allowed the sensor to shift under strong winds.
>
> This problem was mitigated by replacing the adhesive with two stainless-steel pipe clamps. The clamps hold the anemometer firmly against the mast and can be easily undone, allowing the sensor to be removed for maintenance.

**Changes made:** a passive opening for the initial setup; a *we noticed → Upon investigation, we learned* diagnosis; "This problem was mitigated by…"; a closing sentence on what the new design *allows*. The original's "after a few days" became "for an extended period" (the author's phrase), and "work fine" became a concrete functional statement without upgrading it to an unmeasured claim.

### H.4 Equation integration (topic: water-tank sizing)

**Generic:**
> We worked out the tank size from daily use times days of storage, divided by how much of the tank is usable.

**In the author's style:**
> The required volume of the storage tank is given by Equation 3.1:
>
> $$\mathrm{V_{tank} = \frac{Q_{daily} \times D}{\eta}}$$
>
> $\mathrm{V_{tank}}$ is the required tank volume in litres, $\mathrm{Q_{daily}}$ is the daily water consumption in litres, $\mathrm{D}$ is the number of days of storage, and $\mathrm{\eta}$ is the fraction of the tank volume that is usable. Thus, this equation was used to determine the size of the tank for each household.

**Changes made:** a colon lead-in naming "Equation N"; a display equation with upright symbols; a gloss sentence starting with the symbol and giving units; a *Thus* sentence stating the use.

---

## I. Boundaries and failure modes

1. **Copying distinctive passages.** Do not reuse full sentences from the excerpts, especially recognisable ones ("If measured and controlled, the growth rate of the plants would have been significantly greater"; "usher in a transformative era"). Reuse *frames* with the slots refilled from the user's content (D.2).
2. **Importing topic and conclusions.** Never bring in hydroponics, plant growth, IoT boards, XGBoost, cost in Taka, Bangladesh, or claims of beating prior work unless the user's task is about them. The guide's examples are about shape, not subject.
3. **Exaggerating quirks.** The figure-anchoring, *we noticed / Upon investigation*, and *Therefore, maintaining…* are strong habits, but each appears a handful of times per chapter, not in every paragraph. Budget for a 1,000-word section: at most 1 discovery chain, 2–4 figure-led openers (only if figures exist), 1 too-high/too-low pair, and 1–2 *Thus/Therefore* closers.
4. **Reproducing errors as traits.** Treat these as **probable mistakes, not style**:
   - no space before parentheses ("conductivity(EC)", "Light-Emitting-Diodes(LEDs)");
   - *A* before vowel sounds ("A Electrically Isolated…", "A Ultrasonic…");
   - spelling slips ("Searborn", "Altas", "Nurient", "Comparsion", "browing", "solenoid value");
   - definition errors (micronutrients described with the macronutrient definition, Chapter2.tex:35; "Light and Emitting Diode" in the acronym list);
   - copy-paste leftovers (the "pH sensor" sampling sentence under the water-temperature sensor, Chapter4.tex:386);
   - a sentence fragment ("As much as once every 5-6 hours.", Chapter4.tex:324);
   - an unfinished sentence ("It would lead to a lower We have contacted…", Chapter6.tex:47);
   - a stray singular pronoun in a team report ("which he meticulously analyzed", Chapter4.tex:1492);
   - proposal-era *will* in completed-work sections;
   - "Figure N" used for a table (Chapter5.tex:82);
   - over-split conditionals ("Suppose the concentration falls or exceeds the optimal range. In that case, …", Chapter4.tex:77).

   Write the clean version of each.
   **Meaningful unconventional choices to keep:** digits for small counts; deliberate verbatim repetition across parallel units; heavy use of one-sentence figure-intro paragraphs; "per the [needs]"; "such that"; long descriptive headings.
5. **Mechanical sameness.** Rotate schematics (D.2). Vary openers between subject-first, *Figure N*, a connective, and a subordinate clause (*Due to…*, *After…*, *Upon…*, *Since…*). Let some paragraphs be one sentence and some four.
6. **Unsupported claims, citations or confidence.** The author's flat confidence is a *placement* habit (claims stated directly, hedges on numbers). Do not supply bigger effects, "outperforms all previous works", counterfactual certainties, citation numbers, datasheet specs or statistics the user did not provide. If the template wants a number you lack, leave a clearly marked placeholder ([value]) or omit the clause.
7. **Flattening into generic academic prose.** The usual drift is toward smooth, varied, abstract sentences with *this paper argues*, *notably*, *moreover*, em dashes and nominalisations. Counter it by restoring the *we*-narrator, naming concrete components and quantities, anchoring to figures and tables, and turning parallel content into numbered lists.
8. **Overusing the elevated register.** See C-11. If a draft contains more than one of *pivotal / underscores / transformative / realm / delve / meticulous* outside a closing vision paragraph, rewrite it plainly.

---

## J. Drafting and revision workflow

1. **Identify the genre and the section type.** Map the request to an abstract, introduction, background, related work, methods, results, conclusion, caption or acknowledgement (F). If none fits, use the closest one and keep C-1, C-4 (if visuals exist), C-6, C-9 and E.
2. **Inventory the user's facts.** List the components, numbers, figures, tables, sources and changes the user has supplied. These fill the slots. Note what is missing; do not invent it.
3. **Choose blueprints.** Pick from D.3 (P1–P8). Decide the parallel skeleton if there are several like units (C-3).
4. **Draft.** Use the *we*-narrator for decisions and the passive for operations. Write mid-length sentences, paragraphs of two to four sentences, a colon lead-in before each list, "Figure N shows…" for each visual, and an end-of-sentence citation placement.
5. **Signpost** (multi-section documents only): opening scope sentence and closing hand-off (C-8).
6. **Revise against the checklist below**, then reread once purely for errors in I-4.

### Prioritized checklist

1. ☐ Is the narrator a collective *we* (no *I*, no *you*), with *our proposed [system/method]* where natural, and is its density right for the section (sparse in background and related work, dense in iteration, results and conclusion; C-1)?
2. ☐ Are decisions and discoveries in active *we*-clauses and mechanisms or procedures in the passive?
3. ☐ Does every visual or table have an introducing sentence ("Figure N shows…", "as seen in Figure N", "Table N lists…")?
4. ☐ Are enumerable contents in numbered lists with a colon lead-in and full-sentence items?
5. ☐ Where something changed, is it told as trial → noticed → learned → led us to → result?
6. ☐ Are claims stated directly, with hedges on quantities and anomalies only, and **no more certainty than the user's input supports**?
7. ☐ Are components, quantities and units concrete, with digits for counts and abbreviations defined in parentheses with a space before "("?
8. ☐ Do background paragraphs follow define → mechanism → *However/Conversely* extremes → *Therefore, maintaining…*?
9. ☐ Do paragraphs end on a consequence (*Thus*, *This allows*, *This led us to*)?
10. ☐ Are sentences mostly 15–25 words, with no em dashes, semicolons, questions, exclamations, contractions or *e.g.*?
11. ☐ Are parallel units built on the same skeleton, with each slot verified?
12. ☐ Is the elevated vocabulary absent, or confined to one closing paragraph?
13. ☐ Are no source sentences, topics, numbers or citations imported?
14. ☐ Are the I-4 error types (spacing, *a/an*, fragments, pronoun slips, tense drift) absent?

---

## K. Evidence, coverage and limitations

### K.1 What was analysed

- **Document:** `index.tex` (main entry), which `\input`s `Chapters/Chapter1.tex` to `Chapter6.tex` (Introduction, Preliminaries, Related Work, Methodology, Results, Conclusion) and `Appendix.tex` (acronym list). Front matter (Declaration, Abstract, Acknowledgements) is inline in `index.tex`. Chapter 7 is commented out.
- **Read in full, in order:** the abstract, acknowledgements, all six chapters (about 25,800 source words, about 18,100 words of running prose after stripping), the appendix, and captions. Commented-out drafts inside chapters were skimmed only to confirm they are excluded from the build. They were **not** used as evidence, except to note that they share the same voice.
- **Excluded as non-authorial or not part of the document:** `Thesis.cls` and bundled `.sty` files (template and packages); `IEEEtran.bst`, `elsarticle-num.bst`, `IEEEfull.bib`, `mybib.bib` (bibliographic data); `mux_algo.tex` (a reversible-multiplexer algorithm from an unrelated template, not included); `dedicated.tex` (placeholder "Omuk…", not included); the stale `index.pdf`/`.lof`/`.lot` shipped in the archive; the Declaration of Authorship text (template boilerplate).
- **Measurements:** produced by a script over the included prose (method in D.1); keyword counts by `grep` on non-comment source lines. Counts are approximate because of LaTeX stripping and sentence segmentation. They cover the whole included text, not a sample.

### K.2 Compilation status

- Built with **pdfLaTeX + BibTeX** (pdfLaTeX → BibTeX → pdfLaTeX × 2, `-no-shell-escape`, nonstop mode) on TeX Live 2023 in a separate working copy. Output: **139 pages**, all chapters, figures, equations, tables, bibliography and appendix present. Pages 9, 40 and 110 were checked visually as rendered images. The appendix and the dropped-text check below were done on extracted text. Page numbers in this guide are the **printed** page numbers, verified page by page. In this build, the table of contents lags the printed numbers by one from mid-Chapter 4 onward (for example, it lists Results at p. 100, but the chapter starts on printed p. 99).
- **Build repairs (working copy only; no prose changed):**
  1. `bbding.sty` was missing. A stub was added mapping `\Checkmark` to `pifont`'s ✓.
  2. `chemformula.sty` was missing. A stub `\ch{}` was added that subscripts digits (renders KNO₃ and similar correctly).
  3. `algorithm2e.sty` was missing. An empty stub was added that accepts options (the package is loaded but unused in the included text).
  4. `IEEEabrv.bib` was missing. An empty stub was added; without it BibTeX aborted and every citation was undefined.
  5. Two `.eps` figures were converted to PDF with Ghostscript, because shell-escape conversion was disabled.
- **Remaining problems from the source itself (not fixed):**
  - the abstract's `\abstract{` is never closed (recovered automatically and renders correctly);
  - undefined `\Our` and `\hl` in the comparison table, so its last row reads "Proposed system" without "Our";
  - an unclosed `\textcolor{` at Chapter3.tex:361 **silently drops two sentences from the PDF** (the example of deep-neural-network control); they were analysed from source;
  - raw `^` outside math in two table headers, a nested `$` in the NaOH formula (Chapter4.tex:745), and `&` in two bibliography entries;
  - an undefined `appendices` environment;
  - one missing BibTeX key (`ifas2`) and one empty `\ref{}` (Chapter4.tex:874, shows "Figure ??");
  - duplicate labels;
  - the Results chapter's running header says "Chapter 6".

  The PDF is about 45 MB because of uncompressed photographs.

### K.3 Authorship uncertainty

- The thesis is a **two-candidate group report**, and the prose uses *we* throughout. The stray "which **he** meticulously analyzed" (Chapter4.tex:1492) suggests at least one passage was edited by, or about, a single person.
- **Register split:** the ornate vocabulary cluster (C-11) is concentrated in Ch2 §2.3 and the opening and scaling paragraphs of Ch6. The opening Ch6 paragraphs are wrapped in `\textcolor{black}{…}`, a revision-marking convention the authors used across the document for edited passages; the scaling paragraphs are not. Ch3 has none of this vocabulary. These passages may come from a different drafter, a later editing pass, or writing tools. The guide therefore models the **dominant plain voice** of Ch1, Ch3, Ch4, Ch5 and the plain half of Ch6, and treats the ornate layer as secondary.
- Technical descriptions of commercial sensors (Ch2) may paraphrase vendor documentation (they are cited to datasheets and vendor pages), so their phrasing is weaker evidence of personal style than the methods narrative.

### K.4 Limits on the conclusions

- One document, one genre (an undergraduate engineering thesis). There is no evidence for how the author writes papers under page limits, emails, proposals, reviews or non-technical prose. Section F covers only genres present.
- The voice may partly reflect supervisor or department conventions (for example, the per-work Contributions/Limitations template).
- Statistical figures describe this manuscript. Use them for calibration, not as quotas.

---

## L. Validation demonstration

Written using **only** this guide, on a topic unrelated to the source (a campus cafeteria's lunch queue). **Newly written; all facts are invented for illustration.**

> **3.2 Redesign of the Ordering Process**
>
> In this section, we discuss the changes made to the ordering process of the central cafeteria and how they affected the waiting time of students during peak hours.
>
> We started the work by observing the existing ordering process over 5 weekdays. Figure 3.1 shows the layout of the cafeteria, along with the positions of the order counter, the cashier, and the serving counter. A single queue was used for both ordering and payment, after which students moved to the serving counter to collect their meals.
>
> Our initial approach was to add a second cashier beside the order counter. However, after running the cafeteria with two cashiers for 3 days, we noticed that the mean waiting time fell by only 2 minutes. Upon investigation, we learned that the bottleneck was not the payment itself but the time students spent choosing their meals once they reached the counter. This led us to introduce a pre-ordering system, which works as follows:
>
> 1. A menu board is placed at the entrance of the queue, so that students can decide on their meals while waiting in line.
> 2. Each student fills in a numbered token with their order and hands it in at the counter.
> 3. The token number is called out at the serving counter once the meal is ready.
>
> Table 3.2 compares the mean waiting time for the three arrangements. The pre-ordering system reduced the mean waiting time from 18.4 minutes to 7.9 minutes, a 57.07% reduction. This highlights the efficacy of moving the choice of meals away from the counter, where it previously held up the entire queue. The waiting time on Friday was noticeably higher for all three arrangements. This was most likely due to the shorter lunch break on Fridays, which compresses the same number of students into a smaller window.
>
> As we have covered the redesign of the ordering process, in the next section, we will go over the cost of implementing it across the other cafeterias on campus.

**Assessment against the source.**

- *Reproduced well:* the *we*-narrator with a passive for procedure; a scope opener and a hand-off closer (C-8, compare Chapter3.tex:365); the initial approach → *we noticed* → *Upon investigation, we learned* → *This led us to* chain (C-2, compare Chapter4.tex:324–326); "Figure N shows…" and "Table N compares…" anchoring; a colon-led numbered list with full-sentence items; digits for counts; a two-decimal percentage; an anomaly explained with "most likely due to" (compare Chapter5.tex:206); no em dashes, semicolons, questions or *e.g.*; sentence lengths mostly 15–30 words.
- *How the check was done:* the passage was run through the same statistics script used on the thesis (D.1) and read side by side with Chapter3.tex:365, Chapter4.tex:324–326 and Chapter5.tex:206.
  - Sentence length: median 20 words (source 19), maximum 29. No semicolons, dashes or *e.g.*
  - *We/our*: about 27 per 1,000 words, double the thesis-wide average of about 13. This is within the range of the source's iteration and results passages (about 24–43).
- *Two problems the check exposed, and the guide revisions they caused:*
  1. The guide gave no section-level guidance on *we* density, so a model could put the narrator into background or related-work prose, which in the source is nearly impersonal (about 6–7 per 1,000 words). The per-section densities were added to C-1.
  2. The first version of the results paragraph reported the reduction and the Friday anomaly but gave no interpretation of the main result. Every results paragraph in the source does (P6). Rule I-6 against unsupported claims had been over-applied. A "do not under-correct" limit was added to C-6, and the demonstration gained the interpretive sentence beginning "This highlights the efficacy of…".
- *Remaining limitations:* the passage is too short to exercise the author's long-form habits (paired Initial/Current subsections, Contributions/Limitations modules, the economic-derivation chain, background P1/P2 blueprints). It has not been judged by a human reader who knows the thesis, and no similarity score is claimed.
