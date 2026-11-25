package com.theunwritten.theunwrittenmod.race;

import java.util.Map;
import java.util.Objects;

/** Immutable data definition for a race. Missing coefficients are neutral (1.0). */
public record RaceDefinition(
        RaceId id,
        String displayName,
        Map<Characteristic, Double> characteristicMultipliers,
        Map<ResourceType, Double> resourceMultipliers,
        String affinityKey
) {
    public RaceDefinition {
        Objects.requireNonNull(id);
        Objects.requireNonNull(displayName);
        Objects.requireNonNull(affinityKey);
        characteristicMultipliers = Map.copyOf(characteristicMultipliers);
        resourceMultipliers = Map.copyOf(resourceMultipliers);
        characteristicMultipliers.forEach((key, value) -> validate(value, id + "." + key));
        resourceMultipliers.forEach((key, value) -> validate(value, id + "." + key));
    }

    public double characteristicMultiplier(Characteristic key) {
        return characteristicMultipliers.getOrDefault(key, 1.0);
    }

    public double resourceMultiplier(ResourceType key) {
        return resourceMultipliers.getOrDefault(key, 1.0);
    }

    private static void validate(double value, String key) {
        if (!Double.isFinite(value) || value < 0.90 || value > 1.10) {
            throw new IllegalArgumentException("Racial multiplier outside 0.90..1.10: " + key + "=" + value);
        }
    }
}
