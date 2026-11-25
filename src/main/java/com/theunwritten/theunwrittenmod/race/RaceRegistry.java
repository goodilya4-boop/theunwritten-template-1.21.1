package com.theunwritten.theunwrittenmod.race;

import java.util.EnumMap;
import java.util.Map;

/** Central source of race coefficients. Coefficients mirror the current balance workbook. */
public final class RaceRegistry {
    private static final Map<RaceId, RaceDefinition> RACES = create();

    private RaceRegistry() {}

    public static RaceDefinition get(RaceId id) {
        RaceDefinition definition = RACES.get(id);
        if (definition == null) throw new IllegalArgumentException("Unknown race: " + id);
        return definition;
    }

    public static Map<RaceId, RaceDefinition> all() {
        return RACES;
    }

    private static Map<RaceId, RaceDefinition> create() {
        EnumMap<RaceId, RaceDefinition> races = new EnumMap<>(RaceId.class);
        races.put(RaceId.HUMAN, make(RaceId.HUMAN, "Человек",
                stats(1,1,1,1,1,1), resources(1,1,1), "adaptability"));
        races.put(RaceId.ELF, make(RaceId.ELF, "Эльф",
                stats(.90,1.10,.90,1.10,1.10,1), resources(.95,.95,1.05), "natural_perception"));
        races.put(RaceId.DWARF, make(RaceId.DWARF, "Гном",
                stats(1,.90,1.10,1.10,1,.90), resources(1,1,1), "craft_engineering"));
        races.put(RaceId.ORC, make(RaceId.ORC, "Орк",
                stats(1.10,1,1.10,1,1,.90), resources(1,1,.95), "harsh_survival"));
        races.put(RaceId.DRAGONBORN, make(RaceId.DRAGONBORN, "Драконорождённый",
                stats(1.10,.90,1.10,1,1,1.10), resources(1.10,1.05,1.05), "dragon_blood"));
        races.put(RaceId.VOIDBORN, make(RaceId.VOIDBORN, "Пустотный",
                stats(1,1,1,1,1,1), resources(1,1,1), "void_affinity"));
        return Map.copyOf(races);
    }

    private static RaceDefinition make(RaceId id, String name,
            Map<Characteristic,Double> stats, Map<ResourceType,Double> resources, String affinity) {
        return new RaceDefinition(id, name, stats, resources, affinity);
    }

    private static Map<Characteristic,Double> stats(double str,double dex,double con,
            double intel,double wis,double cha) {
        EnumMap<Characteristic,Double> m = new EnumMap<>(Characteristic.class);
        m.put(Characteristic.STR,str); m.put(Characteristic.DEX,dex);
        m.put(Characteristic.CON,con); m.put(Characteristic.INT,intel);
        m.put(Characteristic.WIS,wis); m.put(Characteristic.CHA,cha);
        return m;
    }

    private static Map<ResourceType,Double> resources(double hp,double stamina,double mana) {
        EnumMap<ResourceType,Double> m = new EnumMap<>(ResourceType.class);
        m.put(ResourceType.HP,hp); m.put(ResourceType.STAMINA,stamina);
        m.put(ResourceType.MANA,mana);
        return m;
    }
}
