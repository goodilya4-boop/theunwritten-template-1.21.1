package com.theunwritten.theunwrittenmod.character;

import com.theunwritten.theunwrittenmod.TheUnwritten;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;
import net.neoforged.neoforge.network.handling.DirectionalPayloadHandler;
import net.minecraft.server.level.ServerPlayer;

/** Small server-authoritative request/snapshot channel for the character screen. */
public final class CharacterNetwork {
    private CharacterNetwork() {}

    public record Data(int action, int attribute, int level, int points,
                       int strength, int dexterity, int constitution, int intelligence, int wisdom, int charisma,
                       double racialStrength, double racialDexterity, double racialConstitution, double racialIntelligence, double racialWisdom, double racialCharisma,
                       double health, double maxHealth, double stamina, double maxStamina, double mana, double maxMana,
                       double force, double speed, double reaction, double coordination, double durability, double willpower)
            implements CustomPacketPayload {
        public static final Type<Data> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath(TheUnwritten.MODID, "character_data"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Data> STREAM_CODEC = StreamCodec.of(
                (buf, d) -> {
                    buf.writeVarInt(d.action); buf.writeVarInt(d.attribute); buf.writeVarInt(d.level); buf.writeVarInt(d.points);
                    buf.writeVarInt(d.strength); buf.writeVarInt(d.dexterity); buf.writeVarInt(d.constitution);
                    buf.writeVarInt(d.intelligence); buf.writeVarInt(d.wisdom); buf.writeVarInt(d.charisma);
                    buf.writeDouble(d.racialStrength); buf.writeDouble(d.racialDexterity); buf.writeDouble(d.racialConstitution); buf.writeDouble(d.racialIntelligence); buf.writeDouble(d.racialWisdom); buf.writeDouble(d.racialCharisma);
                    buf.writeDouble(d.health); buf.writeDouble(d.maxHealth); buf.writeDouble(d.stamina); buf.writeDouble(d.maxStamina);
                    buf.writeDouble(d.mana); buf.writeDouble(d.maxMana); buf.writeDouble(d.force); buf.writeDouble(d.speed);
                    buf.writeDouble(d.reaction); buf.writeDouble(d.coordination); buf.writeDouble(d.durability); buf.writeDouble(d.willpower);
                },
                buf -> new Data(buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readVarInt(),
                        buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readVarInt(),
                        buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble(),
                        buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble(),
                        buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble(), buf.readDouble()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public static void register(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar("1");
        registrar.playBidirectional(Data.TYPE, Data.STREAM_CODEC,
                new DirectionalPayloadHandler<>(CharacterClient::handle, CharacterNetwork::handleServer));
    }

    private static void handleServer(Data request, IPayloadContext context) {
        if (!(context.player() instanceof ServerPlayer player)) return;
        CharacterData data = player.getData(CharacterAttachments.CHARACTER);
        if (request.action() == 1 && request.attribute() >= 0 && request.attribute() < 6) {
            String id = switch (request.attribute()) {
                case 0 -> "strength"; case 1 -> "dexterity"; case 2 -> "constitution";
                case 3 -> "intelligence"; case 4 -> "wisdom"; default -> "charisma";
            };
            if (data.availablePoints() > 0) data.setAttribute(id, data.attribute(id) + 1);
        }
        CharacterAttributeSync.apply(player);
        CharacterStats s = data.stats();
        var racial = CharacterStats.racialAttributes(data);
        PacketDistributor.sendToPlayer(player, new Data(2, -1, data.level(), data.availablePoints(),
                data.strength(), data.dexterity(), data.constitution(), data.intelligence(), data.wisdom(), data.charisma(),
                racial.get(com.theunwritten.theunwrittenmod.race.Characteristic.STR), racial.get(com.theunwritten.theunwrittenmod.race.Characteristic.DEX), racial.get(com.theunwritten.theunwrittenmod.race.Characteristic.CON), racial.get(com.theunwritten.theunwrittenmod.race.Characteristic.INT), racial.get(com.theunwritten.theunwrittenmod.race.Characteristic.WIS), racial.get(com.theunwritten.theunwrittenmod.race.Characteristic.CHA),
                data.health(), s.maxHealth(), data.stamina(), s.maxStamina(), data.mana(), s.maxMana(),
                s.physicalForce(), s.speed(), s.reaction(), s.coordination(), s.bodyDurability(), s.willpower()));
    }
}
