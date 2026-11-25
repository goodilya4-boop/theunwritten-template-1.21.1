package com.theunwritten.theunwrittenmod.character;

import com.theunwritten.theunwrittenmod.TheUnwritten;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

@EventBusSubscriber(modid = TheUnwritten.MODID, value = Dist.CLIENT)
public final class CharacterKeybindHandler {
    private CharacterKeybindHandler() {}
    @SubscribeEvent public static void tick(ClientTickEvent.Post event) {
        Minecraft minecraft = Minecraft.getInstance();
        while (CharacterKeybinds.OPEN.consumeClick()) {
            if (minecraft.player != null && minecraft.screen == null) minecraft.setScreen(new CharacterScreen());
        }
    }
}
