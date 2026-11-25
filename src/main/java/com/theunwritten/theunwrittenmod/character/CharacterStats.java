package com.theunwritten.theunwrittenmod.character;

import com.theunwritten.theunwrittenmod.race.Characteristic;
import com.theunwritten.theunwrittenmod.race.RaceId;
import com.theunwritten.theunwrittenmod.race.RaceModifierService;
import com.theunwritten.theunwrittenmod.race.ResourceType;

import java.util.EnumMap;
import java.util.Map;

/**
 * Derived character values calculated from race-adjusted attributes.
 * Resource racial multipliers are applied once, inside their respective formulas.
 */
public record CharacterStats(double physicalForce, double speed, double reaction, double coordination,
                             double bodyDurability, double maxHealth, double maxStamina,
                             double maxMana, double willpower) {
    public static CharacterStats calculate(CharacterData c) {
        Map<Characteristic, Double> adjusted = RaceModifierService.applyCharacteristics(
                toRaceId(c.race()), baseAttributes(c));

        double s = adjusted.get(Characteristic.STR) / 10.0;
        double d = adjusted.get(Characteristic.DEX) / 10.0;
        double t = adjusted.get(Characteristic.CON) / 10.0;
        double i = adjusted.get(Characteristic.INT) / 10.0;
        double w = adjusted.get(Characteristic.WIS) / 10.0;
        double h = adjusted.get(Characteristic.CHA) / 10.0;

        RaceId race = toRaceId(c.race());
        double hpRace = RaceModifierService.resourceMultiplier(race, ResourceType.HP);
        double staminaRace = RaceModifierService.resourceMultiplier(race, ResourceType.STAMINA);
        double manaRace = RaceModifierService.resourceMultiplier(race, ResourceType.MANA);

        return new CharacterStats(
                10 * Math.pow(s, .9) * Math.pow(t, .1),
                10 * Math.pow(d, .8) * Math.pow(s, .2),
                10 * Math.pow(d, .7) * Math.pow(w, .3),
                10 * Math.pow(d, .85) * Math.pow(w, .15),
                10 * Math.pow(t, .9) * Math.pow(s, .1),
                100 * Math.pow(t, .9) * hpRace,
                100 * Math.pow(t, .8) * Math.pow(w, .2) * staminaRace,
                100 * Math.pow(i, .5) * Math.pow(w, .5) * manaRace,
                10 * Math.pow(w, .7) * Math.pow(h, .3));
    }

    /** Returns the stored, unmodified character attributes. */
    public static Map<Characteristic, Double> baseAttributes(CharacterData c) {
        EnumMap<Characteristic, Double> values = new EnumMap<>(Characteristic.class);
        values.put(Characteristic.STR, (double) c.strength());
        values.put(Characteristic.DEX, (double) c.dexterity());
        values.put(Characteristic.CON, (double) c.constitution());
        values.put(Characteristic.INT, (double) c.intelligence());
        values.put(Characteristic.WIS, (double) c.wisdom());
        values.put(Characteristic.CHA, (double) c.charisma());
        return Map.copyOf(values);
    }

    public static Map<Characteristic, Double> racialAttributes(CharacterData c) {
        return RaceModifierService.applyCharacteristics(toRaceId(c.race()), baseAttributes(c));
    }

    private static RaceId toRaceId(Race race) {
        return RaceId.valueOf(race.name());
    }
}
