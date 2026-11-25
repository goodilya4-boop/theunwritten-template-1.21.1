package com.theunwritten.theunwrittenmod.character;

import com.mojang.serialization.Codec;
import net.minecraft.network.chat.Component;

/**
 * Playable race definitions for the first race-selection test.
 * Race lore is descriptive only; no unapproved balance modifiers are applied.
 */
public enum Race {
    HUMAN("human"),
    ELF("elf"),
    DWARF("dwarf"),
    ORC("orc"),
    DRAGONBORN("dragonborn"),
    VOIDBORN("voidborn");

    public static final Codec<Race> CODEC = Codec.STRING.xmap(Race::byId, Race::id);

    private final String id;

    Race(String id) {
        this.id = id;
    }

    public String id() {
        return id;
    }

    public Component displayName() {
        return Component.translatable("race.theunwritten." + id);
    }

    public Component description() {
        return Component.translatable("race.theunwritten." + id + ".description");
    }

    public static Race byId(String id) {
        for (Race race : values()) {
            if (race.id.equalsIgnoreCase(id)) return race;
        }
        return HUMAN;
    }
}
