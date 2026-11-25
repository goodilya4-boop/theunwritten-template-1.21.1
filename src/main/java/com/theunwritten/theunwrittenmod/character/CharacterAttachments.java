package com.theunwritten.theunwrittenmod.character;

import com.theunwritten.theunwrittenmod.TheUnwritten;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;
import java.util.function.Supplier;

public final class CharacterAttachments {
    private CharacterAttachments() {}
    public static final DeferredRegister<AttachmentType<?>> TYPES =
            DeferredRegister.create(NeoForgeRegistries.ATTACHMENT_TYPES, TheUnwritten.MODID);
    public static final Supplier<AttachmentType<CharacterData>> CHARACTER =
            TYPES.register("character", () -> AttachmentType.builder(CharacterData::new)
                    .serialize(CharacterData.CODEC).copyOnDeath().build());
}
