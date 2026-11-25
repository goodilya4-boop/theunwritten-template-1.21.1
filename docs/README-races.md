# Race attributes (Minecraft 1.21.1)

Race definitions and the modifier service are in
`src/main/java/com/theunwritten/theunwrittenmod/race`.

## Current balanced coefficients — code is the source of truth

The following are the **final post-balance values currently implemented in `RaceRegistry.java`**. These values supersede earlier experimental coefficients in design documents and balance drafts. Do not change the code to match older draft tables unless a new balance decision is made.

Characteristic multipliers are applied to the stored base attributes once, before derived-stat formulas. Resource multipliers are applied once inside the corresponding maximum-resource formula.

| Race | STR | DEX | CON | INT | WIS | CHA | HP | Stamina | Mana |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Human | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Elf | 0.90 | 1.10 | 0.90 | 1.10 | 1.10 | 1.00 | 0.95 | 0.95 | 1.05 |
| Dwarf | 1.00 | 0.90 | 1.10 | 1.10 | 1.00 | 0.90 | 1.00 | 1.00 | 1.00 |
| Orc | 1.10 | 1.00 | 1.10 | 1.00 | 1.00 | 0.90 | 1.00 | 1.00 | 0.95 |
| Dragonborn | 1.10 | 0.90 | 1.10 | 1.00 | 1.00 | 1.10 | 1.10 | 1.05 | 1.05 |
| Voidborn | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Integration contract
1. Resolve base stats, progression and allocated stat points.
2. Apply `RaceModifierService.applyCharacteristics(raceId, preRaceFinalValues)` exactly once.
3. Use the returned characteristic values for derived-stat calculations.
4. Do not reapply race characteristic modifiers in derived-stat formulas.
5. Multiply each resource's base maximum formula by
   `RaceModifierService.resourceMultiplier(raceId, ResourceType.HP/STAMINA/MANA)`
   exactly once. Do not multiply the resulting value again.
6. When race changes, recalculate derived values and clamp current resources to their new maxima.

Human is the neutral baseline. Coefficients are currently validated to the inclusive range 0.90–1.10 by `RaceDefinition`.

## Race identifiers and affinity keys

| Race | Affinity key |
|---|---|
| Human | `adaptability` |
| Elf | `natural_perception` |
| Dwarf | `craft_engineering` |
| Orc | `harsh_survival` |
| Dragonborn | `dragon_blood` |
| Voidborn | `void_affinity` |

Affinity keys are registered metadata; they do not currently implement skills, knowledge, profession restrictions, or passive abilities.

## Not implemented
No racial profession locks, free skills/knowledge, passive ability effects, Dragonborn resistances, or Voidborn special effects are implemented in this pass.
