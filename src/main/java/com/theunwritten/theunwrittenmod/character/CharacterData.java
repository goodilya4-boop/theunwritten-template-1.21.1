package com.theunwritten.theunwrittenmod.character;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * Persistent server-authoritative Character Core state.
 * v0.1.0 implements only the character foundation; race and discipline data are intentionally deferred.
 */
public final class CharacterData {
    public static final int STARTING_ATTRIBUTE = 10;
    public static final Codec<CharacterData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            Codec.INT.optionalFieldOf("level", 1).forGetter(d -> d.level),
            Codec.INT.optionalFieldOf("strength", STARTING_ATTRIBUTE).forGetter(d -> d.strength),
            Codec.INT.optionalFieldOf("dexterity", STARTING_ATTRIBUTE).forGetter(d -> d.dexterity),
            Codec.INT.optionalFieldOf("constitution", STARTING_ATTRIBUTE).forGetter(d -> d.constitution),
            Codec.INT.optionalFieldOf("intelligence", STARTING_ATTRIBUTE).forGetter(d -> d.intelligence),
            Codec.INT.optionalFieldOf("wisdom", STARTING_ATTRIBUTE).forGetter(d -> d.wisdom),
            Codec.INT.optionalFieldOf("charisma", STARTING_ATTRIBUTE).forGetter(d -> d.charisma),
            Codec.INT.optionalFieldOf("spent_points", 0).forGetter(d -> d.spentPoints),
            Codec.DOUBLE.optionalFieldOf("health", 100.0).forGetter(d -> d.health),
            Codec.DOUBLE.optionalFieldOf("stamina", 100.0).forGetter(d -> d.stamina),
            Codec.DOUBLE.optionalFieldOf("mana", 100.0).forGetter(d -> d.mana),
            Codec.BOOL.optionalFieldOf("initialized", false).forGetter(d -> d.initialized)
    ).apply(instance, CharacterData::new));

    private int level, strength, dexterity, constitution, intelligence, wisdom, charisma, spentPoints;
    private double health, stamina, mana;
    private boolean initialized;

    public CharacterData() { this(1, 10, 10, 10, 10, 10, 10, 0, 100, 100, 100, false); }

    private CharacterData(int level, int strength, int dexterity, int constitution, int intelligence,
                         int wisdom, int charisma, int spentPoints, double health, double stamina,
                         double mana, boolean initialized) {
        this.level = Math.max(1, level);
        this.strength = valid(strength); this.dexterity = valid(dexterity);
        this.constitution = valid(constitution); this.intelligence = valid(intelligence);
        this.wisdom = valid(wisdom); this.charisma = valid(charisma);
        this.spentPoints = Math.max(0, spentPoints);
        this.health = Math.max(0, health); this.stamina = Math.max(0, stamina);
        this.mana = Math.max(0, mana); this.initialized = initialized;
    }

    private static int valid(int value) { return Math.max(1, value); }
    public int level() { return level; }
    public int strength() { return strength; }
    public int dexterity() { return dexterity; }
    public int constitution() { return constitution; }
    public int intelligence() { return intelligence; }
    public int wisdom() { return wisdom; }
    public int charisma() { return charisma; }
    public int spentPoints() { return spentPoints; }
    public double health() { return health; }
    public double stamina() { return stamina; }
    public double mana() { return mana; }
    public boolean initialized() { return initialized; }

    public int earnedPoints() { return Math.multiplyExact(3, level - 1); }
    public int availablePoints() { return Math.max(0, earnedPoints() - spentPoints); }

    public int attribute(String id) {
        return switch (id) {
            case "strength" -> strength; case "dexterity" -> dexterity;
            case "constitution" -> constitution; case "intelligence" -> intelligence;
            case "wisdom" -> wisdom; case "charisma" -> charisma;
            default -> throw new IllegalArgumentException("Unknown attribute: " + id);
        };
    }

    public boolean setAttribute(String id, int value) {
        value = valid(value);
        int old = attribute(id);
        int cost = value - old;
        if (cost > availablePoints()) return false;
        switch (id) {
            case "strength" -> strength = value; case "dexterity" -> dexterity = value;
            case "constitution" -> constitution = value; case "intelligence" -> intelligence = value;
            case "wisdom" -> wisdom = value; case "charisma" -> charisma = value;
            default -> throw new IllegalArgumentException("Unknown attribute: " + id);
        }
        spentPoints = Math.max(0, spentPoints + cost);
        return true;
    }

    public void setLevel(int value) { level = Math.max(1, value); }
    public void initializeResources() {
        if (!initialized) { health = stats().maxHealth(); stamina = stats().maxStamina(); mana = stats().maxMana(); initialized = true; }
    }
    public void setHealth(double value) { health = clamp(value, stats().maxHealth()); }
    public void setStamina(double value) { stamina = clamp(value, stats().maxStamina()); }
    public void setMana(double value) { mana = clamp(value, stats().maxMana()); }
    private static double clamp(double value, double max) { return Math.max(0, Math.min(value, max)); }
    public CharacterStats stats() { return CharacterStats.calculate(this); }
}
