package com.theunwritten.theunwrittenmod.race;

import java.util.EnumMap;
import java.util.Map;

/**
 * Applies racial coefficients to the final pre-race attribute values exactly once.
 * Call after base values, level progression and allocated points are resolved.
 */
public final class RaceModifierService {
    private RaceModifierService() {}

    public static Map<Characteristic, Double> applyCharacteristics(
            RaceId raceId, Map<Characteristic, Double> preRaceFinalValues) {
        RaceDefinition race = RaceRegistry.get(raceId);
        EnumMap<Characteristic, Double> result = new EnumMap<>(Characteristic.class);
        for (Characteristic characteristic : Characteristic.values()) {
            double value = preRaceFinalValues.getOrDefault(characteristic, 10.0);
            if (!Double.isFinite(value) || value < 0) {
                throw new IllegalArgumentException("Invalid pre-race stat " + characteristic + ": " + value);
            }
            result.put(characteristic, value * race.characteristicMultiplier(characteristic));
        }
        return Map.copyOf(result);
    }

    /** Use this coefficient inside each resource's base formula; don't multiply the result again. */
    public static double resourceMultiplier(RaceId raceId, ResourceType resource) {
        return RaceRegistry.get(raceId).resourceMultiplier(resource);
    }
}
