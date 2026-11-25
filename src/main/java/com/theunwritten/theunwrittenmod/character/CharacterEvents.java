package com.theunwritten.theunwrittenmod.character;

import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

public final class CharacterEvents {
    private CharacterEvents() {}

    public static void onPlayerJoin(EntityJoinLevelEvent event) {
        if (event.getLevel().isClientSide() || !(event.getEntity() instanceof ServerPlayer player)) return;
        CharacterData data = player.getData(CharacterAttachments.CHARACTER);
        data.initializeResources();
        CharacterAttributeSync.apply(player);
    }

    /** Keep character HP persistent while the actual Minecraft health bar is authoritative. */
    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || player.level().isClientSide()) return;
        if (player.tickCount % 20 == 0) CharacterAttributeSync.captureHealth(player);
    }
}
