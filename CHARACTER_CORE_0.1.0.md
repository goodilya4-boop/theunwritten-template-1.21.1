# Character Core 0.1.0

First playable foundation for The Unwritten (Minecraft 1.21.1 / NeoForge).

## Implemented
- Persistent server-side player character data via NeoForge Data Attachment + Mojang Codec.
- Six core attributes, initialized to 10.
- Level and test progression rule: 3 attribute points per level after level 1.
- Attribute point spending with server-side validation.
- Derived values from technical specification v1.0.
- HP / stamina / mana current and maximum values; initialize to computed maximum on first join.
- Death persistence through attachment copy-on-death.
- Persistent test race identity: Human, Elf, Dwarf, Orc, Dragonborn, Voidborn.
- Race selection and inspection commands:
  - `/character race` — show current race and test usage.
  - `/character race <human|elf|dwarf|orc|dragonborn|voidborn>` — switch race for testing.
  - `/character stats` — includes selected race.
  - `/character level <level>` (operator permission level 2).
  - `/character spend <attribute> <amount>` (increment, uses available points).
- Final playtest racial characteristic and resource coefficients from the code's `RaceRegistry`, applied by `RaceModifierService` during derived-stat calculation.
- Basic character screen displaying level, available points, race-adjusted attributes, derived values and resources.
- Client/server data synchronization; point spending is processed server-side.

## Race test scope
Race definitions and final post-balance coefficients are registered in `RaceRegistry`. The selected race is saved with the character attachment. Race characteristic modifiers are applied once to final pre-race attributes before derived-stat calculation; resource modifiers are applied once inside their respective maximum-resource formulas. Human is the neutral baseline.

The values in `docs/README-races.md` and `RaceRegistry.java` are the current balanced implementation values. Older experimental values in design/specification documents are not the source of truth for the current code balance.

Racial profession locks, free skills/knowledge, passive ability effects, Dragonborn resistances, and Voidborn special effects are not implemented in this first pass.

## Deliberately not included
Finalized race abilities and restrictions, mana-channel access, tiers, disciplines, resource spending and regeneration, combat systems, mental-state mechanics, and energy systems remain outside the current Character Core implementation. The character screen and basic network synchronization are implemented.

## Build
Use Java 21 and the repository's configured Gradle/NeoForge MDK. Run `./gradlew build`.
