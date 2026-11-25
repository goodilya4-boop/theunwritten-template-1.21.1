package com.theunwritten.theunwrittenmod.character;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

/**
 * Applies the first test mappings from Character Core values to vanilla player attributes.
 * All modifiers use stable IDs and are replaced, never stacked.
 */
public final class CharacterAttributeSync {
    private static final ResourceLocation HEALTH_ID =
            ResourceLocation.fromNamespaceAndPath("theunwritten", "character_health");
    private static final ResourceLocation SPEED_ID =
            ResourceLocation.fromNamespaceAndPath("theunwritten", "character_speed");
    private static final ResourceLocation DAMAGE_ID =
            ResourceLocation.fromNamespaceAndPath("theunwritten", "character_force");

    private CharacterAttributeSync() {}

    public static void apply(ServerPlayer player) {
        CharacterData character = player.getData(CharacterAttachments.CHARACTER);
        CharacterStats stats = character.stats();

        // Spec v1.0 uses HPmax=100 at Constitution 10. Vanilla player max health is 20.
        replace(player.getAttribute(Attributes.MAX_HEALTH), HEALTH_ID,
                stats.maxHealth() / 20.0 - 1.0, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);

        // Test mapping: Speed is a character-scale value, not a direct vanilla multiplier.
        // Logarithmic diminishing returns keep high Dexterity from making movement uncontrollable.
        // At derived Speed 10 the vanilla speed is unchanged; the bonus is capped at +50%.
        double speedRatio = Math.max(0.01, stats.speed() / 10.0);
        double speedBonus = Math.max(-0.50, Math.min(0.50, 0.15 * Math.log(speedRatio)));
        replace(player.getAttribute(Attributes.MOVEMENT_SPEED), SPEED_ID,
                speedBonus, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);

        // Test mapping only: physical force adds 0.1 attack damage per point above/below baseline 10.
        replace(player.getAttribute(Attributes.ATTACK_DAMAGE), DAMAGE_ID,
                (stats.physicalForce() - 10.0) * 0.1, AttributeModifier.Operation.ADD_VALUE);

        double maxHealth = player.getMaxHealth();
        if (character.health() <= 0.0) character.setHealth(maxHealth);
        player.setHealth((float) Math.min(character.health(), maxHealth));
    }

    private static void replace(AttributeInstance attribute, ResourceLocation id, double amount,
                                AttributeModifier.Operation operation) {
        if (attribute == null) return;
        attribute.removeModifier(id);
        if (Double.isFinite(amount) && Math.abs(amount) > 1.0E-7) {
            attribute.addPermanentModifier(new AttributeModifier(id, amount, operation));
        }
    }

    /** Persist the real vanilla health value into the character attachment. */
    public static void captureHealth(ServerPlayer player) {
        player.getData(CharacterAttachments.CHARACTER).setHealth(player.getHealth());
    }
}
