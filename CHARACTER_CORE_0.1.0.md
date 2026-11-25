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
- Commands:
  - `/character stats`
  - `/character level <level>` (operator permission level 2)
  - `/character spend <attribute> <amount>` (increment, uses available points)

## Deliberately not included
Race modifiers, race selection, mana-channel access, tiers, disciplines, regeneration, combat, GUI, client synchronization, mental state mechanics and energy systems. Those are not finalized in specification v1.0.

## Build
Use Java 21 and the repository's configured Gradle/NeoForge MDK. Run `./gradlew build`.
