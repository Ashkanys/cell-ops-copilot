# Counting & viability measurement (Trypan blue) — Hemocytometer + Countess™ 3

## Purpose
Measure **cell concentration** and **percent viability** using **trypan blue exclusion** with:
- a manual hemocytometer method, and
- a Countess™ 3 automated cell counter,


## Scope
- Applies to mammalian cell suspensions (e.g., after detachment/passaging, thawing, batch validation, etc.).
- Assumes trypan blue exclusion is appropriate for your workflow.
- Does not cover fluorescent viability dyes or flow cytometry-based viability.

## Safety
- Follow your lab biosafety level, waste disposal, and decontamination procedures.
- Wear appropriate PPE and work in a certified BSC when handling live cultures.
- Handle trypan blue per SDS; avoid skin/eye contact and dispose of dye-containing waste per lab rules.

## Materials

### Reagents
- Cell suspension (well-mixed)
- 0.4% trypan blue solution (cell-culture tested)
- 70% Ethanol

### Consumables
- Micropipette + sterile tips
- Hemocytometer (Neubauer) + coverslip
- Countess™ cell counting slides compatible with Countess 3
- 1.5 mL microtubes (or similar) for mixing sample + dye
- Kimwipes/lint-free wipes

### Equipment
- Microscope
- Countess™ 3 Automated Cell Counter

## Preparation
- Label sample tubes with sample ID, date/time, and operator initials.
- Gently resuspend the cell suspension to homogeneity immediately before sampling.
- Inspect trypan blue visually; if it appears cloudy or contains visible particles/debris, **filter it (sterile 0.2–0.22 µm) or use a fresh bottle**.

## Procedure

### A) Prepare the trypan blue mix (common to both methods)
1. Mix the cell suspension gently but thoroughly (avoid foaming).
2. Combine **equal volumes** of cell suspension and **0.4% trypan blue** (typical **1:1**, e.g., 10 µL + 10 µL) in a labeled microtube.
3. Mix by gentle pipetting or quick vortex
4. Count the sample **within 5 minutes** of mixing with trypan blue to avoid time-dependent toxicity artifacts.

---

### B) Hemocytometer counting (manual)
1. Clean the hemocytometer and coverslip and assemble the coverslip correctly (Newton rings visible).
2. Load **10 µL** of the trypan blue–mixed sample into one chamber by capillary action (avoid bubbles/overfilling).
3. Load **10 µL** into the second chamber for the required replicate count.
4. Focus on the grid and count **viable (unstained)** and **non-viable (blue)** cells separately in **four large corner squares** (standard Neubauer practice).
5. Apply a consistent border rule (e.g., **count cells touching top/left borders; exclude bottom/right**) to avoid double counting.
6. Record counts for each chamber separately (Chamber A and Chamber B).

**Calculations (hemocytometer)**
- Average viable cells per large square = (sum of viable cells counted in 4 squares) ÷ 4
- **Viable cells/mL** = (average viable cells per square) × (dilution factor) × **10⁴**
- **Total cells/mL** = (average total cells per square) × (dilution factor) × **10⁴**
- **Viability (%)** = viable ÷ total × 100

**Replicate consistency check (hemocytometer)**
- Compare Chamber A vs Chamber B viable cells/mL.
- If they differ by more than your lab’s threshold (commonly **>10%**), mix again and repeat the count (or prepare a fresh trypan blue mix and re-load).

---

### C) Countess™ 3 counting (automated)
1. Turn on the Countess 3 and select the appropriate **Brightfield / Trypan Blue** protocol.
2. Confirm whether the instrument protocol is set to **apply the 1:1 trypan blue dilution correction** (if you mixed 1:1, the software should account for it).
3. Load **10 µL** of the trypan blue–mixed sample into Chamber 1 of the Countess slide.
4. Load **10 µL** of the same mixture into Chamber 2 of the slide to perform the required replicate count.
5. Insert the slide and run the count.
6. Save or record: viable cells/mL, total cells/mL, viability (%), and any flags (e.g., debris, clumping).

**Replicate consistency check (Countess 3)**
- Compare Chamber 1 vs Chamber 2 viable cells/mL.
- If they differ by more than your lab’s threshold (commonly **>10%**), re-mix the source sample and repeat on a new slide.

---

### D) Reporting
1. Report **viable cells/mL**, **total cells/mL**, and **viability (%)** as the mean of the two replicate counts.
2. Document the method used (Hemocytometer or Countess 3), dilution factor, and any observations (clumping, debris, high dead fraction).

## QC checks / expected observations
- Replicate counts agree within the lab’s predefined threshold (commonly ≤10% difference).
- Viable cells are **unstained**; dead cells are **blue**.
- Minimal clumping and minimal debris; if debris is high, results may be unreliable.

## Troubleshooting
- **Large difference between replicate counts**
  - Likely causes: poor mixing, cells settling, bubbles/overfill in chamber, uneven loading.
  - Actions: mix thoroughly, reload carefully, and repeat with a fresh trypan blue mix if needed.

- **Debris makes it hard to distinguish cells**
  - Likely causes: dirty/precipitated trypan blue, unhealthy culture, harsh detachment.
  - Actions: **filter trypan blue (0.2–0.22 µm) or use fresh**, and consider gentle handling to reduce debris.

- **Clumping**
  - Likely causes: incomplete dissociation, DNA from dead cells, overly dense sample.
  - Actions: gentle trituration, consider dilution, and ensure proper detachment.

- **Viability seems to drop during counting**
  - Likely cause: counting too long after mixing with trypan blue (time-dependent toxicity).
  - Actions: standardize timing and count within 3–5 minutes.

## Critical points
- Always perform **≥2 independent counts** (two hemocytometer chambers or two Countess slide chambers) to confirm consistency.
- Standardize the **staining time** and **count window**; trypan blue becomes toxic over time and can bias viability downward if you wait too long.
- If trypan blue looks **dirty/particle-rich**, **filter it (0.2–0.22 µm) or replace it** before counting, because debris can distort both manual and automated counts.
- Use consistent counting rules (border inclusion/exclusion) for hemocytometer work.

## References
- Thermo Fisher Scientific (Gibco) — Manually counting cells in a hemocytometer (Neubauer grid volume and 10⁴ factor):  
  https://www.thermofisher.com/us/en/home/references/gibco-cell-culture-basics/cell-culture-protocols/counting-cells-in-a-hemacytometer.html

- Pioli (WMich) — Hemocytometer cell counting (example calculations; trypan blue dilution factor):  
  https://med.wmich.edu/sites/default/files/Hemacytometer_Cell_Counting.pdf

- University of Virginia — Cell counting using hemocytometer (viable cells/mL formula and viability %):  
  https://med.virginia.edu/otolaryngology/wp-content/uploads/sites/244/2020/06/Cell-Counting-using-Hemocytometer.pdf

- Strober (2015), *Trypan Blue Exclusion Test of Cell Viability* (count within 3–5 minutes after mixing):  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6716531/

- Thermo Fisher Scientific — Countess 3 Automated Cell Counter User Guide (protocol features; trypan blue handling and dilution correction options):  
  https://documents.thermofisher.com/TFS-Assets/LSG/manuals/MAN0019566_Countess_3_Auto_Cell_Counter_UG.pdf

- Thermo Fisher Scientific — Countess automated cell counter accessories (Countess slides have **two chambers** for duplicate counts; 10 µL + 10 µL trypan blue typical):  
  https://www.thermofisher.com/us/en/home/life-science/cell-analysis/cell-analysis-instruments/automated-cell-counters/accessories.html

- BPS Bioscience — Trypan blue staining protocol (3–5 min timing; trypan blue can form aggregates; filter prior to use):  
  https://bpsbioscience.com/trypan-blue-staining-protocol

- Creighton University — Trypan blue for viability (filtering trypan blue to remove particles):  
  https://www.creighton.edu/sites/default/files/2024-03/Trypan_Blue.pdf
