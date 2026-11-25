package com.theunwritten.theunwrittenmod.character;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

public final class CharacterCommands {
    private CharacterCommands() {}

    public static void register(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("character")
            .then(Commands.literal("stats").executes(ctx -> show(ctx.getSource().getPlayerOrException())))
            .then(Commands.literal("race")
                .executes(ctx -> showRace(ctx.getSource().getPlayerOrException()))
                .then(Commands.literal("human").executes(ctx -> chooseRace(ctx.getSource().getPlayerOrException(), Race.HUMAN)))
                .then(Commands.literal("elf").executes(ctx -> chooseRace(ctx.getSource().getPlayerOrException(), Race.ELF)))
                .then(Commands.literal("dwarf").executes(ctx -> chooseRace(ctx.getSource().getPlayerOrException(), Race.DWARF)))
                .then(Commands.literal("orc").executes(ctx -> chooseRace(ctx.getSource().getPlayerOrException(), Race.ORC)))
                .then(Commands.literal("dragonborn").executes(ctx -> chooseRace(ctx.getSource().getPlayerOrException(), Race.DRAGONBORN)))
                .then(Commands.literal("voidborn").executes(ctx -> chooseRace(ctx.getSource().getPlayerOrException(), Race.VOIDBORN))))
            .then(Commands.literal("level")
                .then(Commands.argument("level", IntegerArgumentType.integer(1))
                    .requires(source -> source.hasPermission(2))
                    .executes(ctx -> {
                        ServerPlayer player = ctx.getSource().getPlayerOrException();
                        CharacterData data = player.getData(CharacterAttachments.CHARACTER);
                        data.setLevel(IntegerArgumentType.getInteger(ctx, "level"));
                        ctx.getSource().sendSuccess(() -> Component.literal("Level set to " + data.level()
                                + ". Available points: " + data.availablePoints()), true);
                        return 1;
                    })))
            .then(Commands.literal("spend")
                .then(Commands.literal("strength").then(Commands.argument("amount", IntegerArgumentType.integer(1))
                    .executes(ctx -> spend(ctx.getSource().getPlayerOrException(), "strength", ctx.getArgument("amount", Integer.class)))))
                .then(Commands.literal("dexterity").then(Commands.argument("amount", IntegerArgumentType.integer(1))
                    .executes(ctx -> spend(ctx.getSource().getPlayerOrException(), "dexterity", ctx.getArgument("amount", Integer.class)))))
                .then(Commands.literal("constitution").then(Commands.argument("amount", IntegerArgumentType.integer(1))
                    .executes(ctx -> spend(ctx.getSource().getPlayerOrException(), "constitution", ctx.getArgument("amount", Integer.class)))))
                .then(Commands.literal("intelligence").then(Commands.argument("amount", IntegerArgumentType.integer(1))
                    .executes(ctx -> spend(ctx.getSource().getPlayerOrException(), "intelligence", ctx.getArgument("amount", Integer.class)))))
                .then(Commands.literal("wisdom").then(Commands.argument("amount", IntegerArgumentType.integer(1))
                    .executes(ctx -> spend(ctx.getSource().getPlayerOrException(), "wisdom", ctx.getArgument("amount", Integer.class)))))
                .then(Commands.literal("charisma").then(Commands.argument("amount", IntegerArgumentType.integer(1))
                    .executes(ctx -> spend(ctx.getSource().getPlayerOrException(), "charisma", ctx.getArgument("amount", Integer.class)))))));
    }

    private static int chooseRace(ServerPlayer player, Race race) {
        CharacterData data = player.getData(CharacterAttachments.CHARACTER);
        data.setRace(race);
        player.sendSystemMessage(Component.translatable("command.theunwritten.race.selected", race.displayName()));
        player.sendSystemMessage(race.description());
        return 1;
    }

    private static int showRace(ServerPlayer player) {
        CharacterData data = player.getData(CharacterAttachments.CHARACTER);
        player.sendSystemMessage(Component.translatable("command.theunwritten.race.current", data.race().displayName()));
        player.sendSystemMessage(Component.translatable("command.theunwritten.race.help"));
        player.sendSystemMessage(data.race().description());
        return 1;
    }

    private static int spend(ServerPlayer player, String attribute, int amount) {
        CharacterData data = player.getData(CharacterAttachments.CHARACTER);
        int target = Math.addExact(data.attribute(attribute), amount);
        if (!data.setAttribute(attribute, target)) {
            player.sendSystemMessage(Component.literal("Not enough points. Available: " + data.availablePoints()));
            return 0;
        }
        player.sendSystemMessage(Component.literal(attribute + " = " + target + " (points left: " + data.availablePoints() + ")"));
        return 1;
    }

    private static int show(ServerPlayer player) {
        CharacterData c = player.getData(CharacterAttachments.CHARACTER);
        CharacterStats s = c.stats();
        player.sendSystemMessage(Component.literal("Character • Level " + c.level() + " • Points " + c.availablePoints()));
        player.sendSystemMessage(Component.translatable("command.theunwritten.race.current", c.race().displayName()));
        player.sendSystemMessage(Component.literal("STR " + c.strength() + " | DEX " + c.dexterity() + " | CON " + c.constitution()
                + " | INT " + c.intelligence() + " | WIS " + c.wisdom() + " | CHA " + c.charisma()));
        player.sendSystemMessage(Component.literal(String.format(java.util.Locale.ROOT,
                "Force %.1f | Speed %.1f | Reaction %.1f | Coordination %.1f | Durability %.1f",
                s.physicalForce(), s.speed(), s.reaction(), s.coordination(), s.bodyDurability())));
        player.sendSystemMessage(Component.literal(String.format(java.util.Locale.ROOT,
                "HP %.1f/%.1f | ST %.1f/%.1f | MP %.1f/%.1f | Will %.1f",
                c.health(), s.maxHealth(), c.stamina(), s.maxStamina(), c.mana(), s.maxMana(), s.willpower())));
        return 1;
    }
}
