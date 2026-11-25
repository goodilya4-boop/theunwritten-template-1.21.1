# Character Core 0.1.0

First playable foundation for The Unwritten (Minecraft 1.21.1 / NeoForge).

## Implemented
- Persistent server-side player character data via NeoForge Data Attachment + Mojang Codec.
- Six core attributes, initialized to 10.
- Level and test progression rule: 3 attribute points per level after level 1.
- Attribute point spending with validation.
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

## Race test scope
Race names and brief descriptions are registered and the selected race is saved with the character attachment. Existing characters and old serialized data default to Human.

Race modifiers and special abilities are intentionally not applied yet: the race-balance sheet contains experimental values, not approved gameplay coefficients. This test checks selection, persistence, and the race data path only.

## Deliberately not included
Race stat modifiers, finalized race abilities, mana-channel access, tiers, disciplines, regeneration, combat, GUI, client synchronization, mental state mechanics and energy systems. These remain outside the current test implementation.

## Build
Use Java 21 and the repository's configured Gradle/NeoForge MDK. Run `./gradlew build`.
