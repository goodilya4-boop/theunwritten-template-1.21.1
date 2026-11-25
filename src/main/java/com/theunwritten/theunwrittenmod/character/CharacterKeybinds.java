package com.theunwritten.theunwrittenmod.character;

import com.theunwritten.theunwrittenmod.TheUnwritten;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import org.lwjgl.glfw.GLFW;

@EventBusSubscriber(modid = TheUnwritten.MODID, value = Dist.CLIENT)
public final class CharacterKeybinds {
    private CharacterKeybinds() {}
    public static final KeyMapping OPEN = new KeyMapping("key.theunwritten.character", InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_K, "key.categories.theunwritten");

    @SubscribeEvent public static void register(RegisterKeyMappingsEvent event) { event.register(OPEN); }
}
