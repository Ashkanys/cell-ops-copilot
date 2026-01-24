# Plating Adherent Cells from Frozen Stock for HTS (384-well)

## Purpose
Plate adherent mammalian cells from frozen cryovials into **384-well plates** for high-throughput screening (HTS).

## Scope
- Plate format: **384-well**
- Does not cover: compound addition, assay readouts, or long-term culture maintenance

## Safety & compliance
- Follow your lab biosafety level and local SOPs for cell handling and waste disposal.
- Use appropriate PPE and work in a certified biosafety cabinet (BSC).
- Handle DMSO-containing cryovials carefully; minimize exposure time at warm temperatures.

## Materials & equipment
- **384-well plates** suitable for adherent cells (TC-treated; coated if required by the cell line)
- Complete growth medium (pre-warmed as appropriate)
- PBS/DPBS (cell-line dependent; often Ca²⁺/Mg²⁺-free for handling)
- Sterile distilled/deionized water (for instrument priming/cleaning)
- 70% ethanol (for surface disinfection and instrument decontamination, per instrument SOP)
- Cryovials of cells (stored in LN₂ vapor phase preferred, or −80 °C short-term)
- 50 mL conical tubes
- Centrifuge
- Cell counter + viability method (automated counter or trypan blue)
- Serological pipettes / pipettor
- Sterile reagent reservoir(s) (as needed)
- Plate seeding instrument (e.g., **Multidrop** or equivalent) with a **saved plating protocol** and the correct cassette
- 37 °C, 5% CO₂ incubator

## Preparation
- Pre-warm complete medium to 37 °C.
- Pre-label plates and record the plate map (including any edge-well strategy).
- Determine the number of plates and wells to be seeded.
- Calculate total cells required using an overage factor (typically 10%) to cover dead volume and dispensing loss.
- Calculate the target suspension concentration using: **cells/mL = cells per well ÷ dispense volume (mL)** (e.g., for 50 µL/well: cells/mL = cells/well ÷ 0.05 = cells/well × 20).
- Stage sterile 50 mL conicals and a waste container in the BSC.
- Prepare priming/cleaning liquids for the dispenser (sterile water, 70% ethanol, PBS) per your instrument SOP.
- Retrieve the required number of 384-well plates and keep them closed until ready to seed.

## Procedure (step-by-step)

### A) Thaw cells in controlled batches
1. Determine the number of vials to thaw based on the calculated total cells needed.
2. Thaw cryovials in batch of 5, quickly in a 37 °C water bath until only a small ice crystal remains (typically ~1–2 min).
3. Wipe each cryovial thoroughly with 70% ethanol and transfer it into the BSC.
4. Transfer the thawed contents **dropwise** into a 50 mL conical containing pre-warmed complete medium (use a consistent dilution volume per vial).

### B) Remove DMSO (typical for DMSO-frozen stocks)
5. Centrifuge the pooled cell suspension at **~200–300 × g for ~5 min** (adjust per cell type and lab practice).
6. Aspirate or decant the supernatant carefully without disturbing the pellet.
7. Resuspend the pellet in a **known volume** of complete medium. (e.g. 100mL)


### C) Count and adjust concentration
8. Mix the suspension gently but thoroughly to ensure uniformity.
9. Remove an aliquot for cell count and viability.
10. Calculate the required cell suspension concentration for plating using the planned dispense volume (e.g., 50 µL/well).
11. Adjust the suspension to the target concentration by adding medium.
12. Mix gently to homogeneity while avoiding foaming.
13. Keep cells uniformly suspended throughout dispensing by gently inverting/swirl-mixing at regular intervals.

### D) Plate using an automated dispenser (example: Multidrop)
14. Install the correct dispensing cassette for the cell type and confirm it is seated properly.
15. Load and verify the saved 384-well cell-seeding protocol (volume, speed, plate type, and prime settings).
16. Prime the cassette with 25 mL of **70% Ethanol**, then **distiiled water**, then **PBS**.
17. Prime the cassette with cell suspension and discard the initial dispensed volume to waste to ensure stable flow.
18. Dispense the programmed volume (e.g., **50 µL/well**) into each 384-well plate according to the saved protocol.
19. Mix the source cell suspension at defined intervals during the run to prevent settling (e.g., every 1–2 plates).
20. Rinse the cassette immediately after dispensing by priming with PBS to remove residual cells.
21. Clean/decontaminate the cassette according to the instrument SOP (commonly PDB → water → 70% ethanol) and store it properly.

### E) Settlement and incubation
22. Cover the plate and keep it flat on a level surface immediately after dispensing.
23. Allow plates to rest at **room temperature for ~30 min** to promote even cell settling and reduce edge effects.
24. Transfer plates carefully to the incubator without jolting or tilting.
25. Incubate under standard conditions (typically 37 °C, 5% CO₂, humidified).


## QC checks / expected observations
- Cell viability after thaw meets the lab’s acceptance threshold for screening.
- Uniform well-to-well appearance shortly after plating (no obvious gradients or streaks).
- Minimal bubbles and minimal visible clumping.
- After attachment (timing is cell-line dependent), cells appear evenly distributed (no strong “ring” patterns beyond expected plate effects).

## Troubleshooting
- **Clumping / streaks in wells**
  - Likely causes: insufficient mixing, high concentration, slow handling after thaw, dispenser start-up instability
  - Actions: increase gentle mixing frequency, reduce time between mixing cycles, discard the initial prime volume, and confirm single-cell suspension before dispensing

- **Low viability after thaw**
  - Likely causes: prolonged warm exposure, slow dilution of DMSO, poor cryostock quality
  - Actions: reduce thaw batch size, speed up dilution/spin steps, and verify cryostock history/age

- **Uneven seeding across a plate**
  - Likely causes: cells settling in the source container, inconsistent mixing, movement before settling, edge effects
  - Actions: mix more frequently, keep plates flat, include a room-temperature rest step, and apply an edge-well strategy

- **Poor attachment**
  - Likely causes: plate surface not appropriate, coating missing/expired, medium mismatch
  - Actions: confirm plate type/coating requirements, verify coating workflow, and confirm media/attachment conditions for the cell line

## Critical points
- Use plates that match the cell line’s attachment requirements (TC-treated and/or coated).
- Thaw quickly and minimize time cells spend in concentrated DMSO at warm temperatures.
- Maintain tight timing from thaw → dilute → pellet → resuspend → count → plate.
- Keep cells uniformly suspended during dispensing (settling is a major HTS variability source).
- Rest plates flat at room temperature before incubation to reduce edge effects and improve uniform distribution.
- Record traceability details (cell lot/vial IDs, passage, viability, target density, dispense volume, plate IDs, operator, timestamps).

## References
- Thermo Fisher (Gibco) — *Thawing Cells* (dropwise dilution into warm medium; typical 200 × g spin to remove DMSO):  
  https://www.thermofisher.com/us/en/home/references/gibco-cell-culture-basics/cell-culture-protocols/thawing-cells.reg.no.html

- ATCC — *Animal Cell Culture Guide* (cryoprotectant removal by gentle centrifugation; general thaw guidance):  
  https://www.atcc.org/resources/culture-guides/animal-cell-culture-guide

- Lundholt et al., 2003 — *A simple technique for reducing edge effect in cell-based assays* (room-temperature pre-incubation improves uniform distribution):  
  https://pubmed.ncbi.nlm.nih.gov/14567784/

- Das et al., 2017 (JoVE / PMC-linked protocol) — 384-well seeding practices including maintaining suspension and room-temperature rest:  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5408984/  
  https://app.jove.com/v/55403/evaporation-reducing-culture-condition-increases-reproducibility

- Thermo Fisher — *SmartTips: Best practices for MultiCombi cassettes (cells)* (prime with PBS; prime with cell suspension):  
  https://assets.fishersci.com/TFS-Assets/LCD/Product-Bulletins/Best-Practices-MultiCombi-Cassettes-Cells-SmartTips-EN.pdf

- Thermo Fisher / FisherSci — *Maintenance guide for cell dispensing with Multidrop Combi* (PBS priming; rinse after dispensing; separate cassettes per cell line):  
  https://assets.fishersci.com/TFS-Assets/LCD/Warranties/D10895~.pdf

- Harvard ICCB — *How to Use the MultiDrop Combi* (example cleaning: water → 70% ethanol → water):  
  https://iccb.med.harvard.edu/file_url/321
