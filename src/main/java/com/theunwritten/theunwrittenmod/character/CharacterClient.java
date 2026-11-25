package com.theunwritten.theunwrittenmod.character;

import net.minecraft.client.Minecraft;
import net.neoforged.neoforge.network.handling.IPayloadContext;

public final class CharacterClient {
    private CharacterClient() {}
    public static void handle(CharacterNetwork.Data data, IPayloadContext context) {
        if (data.action() == 2 && Minecraft.getInstance().screen instanceof CharacterScreen screen) {
            screen.update(data);
        }
    }
}
