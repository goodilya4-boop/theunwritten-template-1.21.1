package com.theunwritten.theunwrittenmod.character;

import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;

public final class CharacterEvents {
    private CharacterEvents() {}
    public static void onPlayerJoin(EntityJoinLevelEvent event) {
        if (event.getLevel().isClientSide() || !(event.getEntity() instanceof ServerPlayer player)) return;
        CharacterData data = player.getData(CharacterAttachments.CHARACTER);
        data.initializeResources();
    }
}
