# Race attributes (1.21.1)

Race data and the first attribute modifier service are in
`src/main/java/com/theunwritten/theunwrittenmod/race`.

## Integration contract
1. Resolve base stats, progression and allocated stat points.
2. Apply `RaceModifierService.applyCharacteristics(raceId, preRaceFinalValues)` once.
3. Use the returned characteristic values for derived-stat calculations.
4. Do not reapply race modifiers in derived-stat formulas.
5. Multiply the resource's existing formula by
   `RaceModifierService.resourceMultiplier(raceId, ResourceType.HP/STAMINA/MANA)`
   exactly once. Avoid applying the multiplier to the result a second time.

All coefficients are constrained to 0.90–1.10. Human is the neutral baseline.
Approved direct values: Dwarf HP/stamina 1.00; Orc HP/stamina 1.00; Elf mana 1.05.
Other coefficient values currently reflect the balance workbook's playtest draft.

No racial profession locks, free skills/knowledge, passive ability effects,
Dragonborn resistances, or Voidborn special effects are implemented in this first pass.
