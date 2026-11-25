package com.theunwritten.theunwrittenmod.character;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.network.PacketDistributor;

public final class CharacterScreen extends Screen {
    private static final String[] NAMES = {"Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"};
    private static final String[] SHORT = {"STR", "DEX", "CON", "INT", "WIS", "CHA"};
    private CharacterNetwork.Data data;
    private Button[] plus = new Button[6];

    public CharacterScreen() { super(Component.translatable("character.theunwritten.title")); }

    @Override protected void init() {
        int left = (width - 300) / 2;
        int top = (height - 250) / 2;
        for (int i = 0; i < 6; i++) {
            final int index = i;
            plus[i] = addRenderableWidget(Button.builder(Component.literal("+"), b -> {
                PacketDistributor.sendToServer(new CharacterNetwork.Data(1, index, 0, 0,
                        0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0));
            }).bounds(left + 255, top + 43 + i * 20, 24, 18).build());
            plus[i].active = false;
        }
        addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> onClose())
                .bounds(left + 110, top + 222, 80, 20).build());
        PacketDistributor.sendToServer(new CharacterNetwork.Data(0, -1, 0, 0,
                0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0));
    }

    /** Prevent vanilla Screen background rendering from applying its fullscreen blur. */
    @Override
    public void renderBackground(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        // The screen draws its own dim layer and panel in render().
    }

    public void update(CharacterNetwork.Data value) {
        data = value;
        for (Button button : plus) if (button != null) button.active = value.points() > 0;
    }

    @Override public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        graphics.fill(0, 0, width, height, 0x70000000);
        int left = (width - 300) / 2, top = (height - 250) / 2;
        graphics.fill(left, top, left + 300, top + 250, 0xB0202020);
        graphics.drawCenteredString(font, title, width / 2, top + 10, 0xFFFFFF);
        if (data == null) {
            graphics.drawCenteredString(font, Component.translatable("character.theunwritten.loading"), width / 2, top + 90, 0xCCCCCC);
        } else {
            graphics.drawString(font, Component.translatable("character.theunwritten.level", data.level()), left + 12, top + 28, 0xE0E0E0);
            graphics.drawString(font, Component.translatable("character.theunwritten.points", data.points()), left + 155, top + 28, 0xE0E0E0);
            double[] values = {data.racialStrength(),data.racialDexterity(),data.racialConstitution(),data.racialIntelligence(),data.racialWisdom(),data.racialCharisma()};
            for (int i=0;i<6;i++) graphics.drawString(font, SHORT[i] + "  " + NAMES[i] + ": " + String.format(java.util.Locale.ROOT, "%.2f", values[i]), left + 15, top + 47 + i*20, 0xFFFFFF);
            graphics.drawString(font, String.format(java.util.Locale.ROOT, "Force %.1f | Speed %.1f | Reaction %.1f",
                    data.force(), data.speed(), data.reaction()), left + 12, top + 180, 0xC8C8C8);
            graphics.drawString(font, String.format(java.util.Locale.ROOT, "Coord. %.1f | Durability %.1f | Will %.1f",
                    data.coordination(), data.durability(), data.willpower()), left + 12, top + 194, 0xC8C8C8);
            graphics.drawString(font, String.format(java.util.Locale.ROOT, "HP %.0f/%.0f   ST %.0f/%.0f   MP %.0f/%.0f",
                    data.health(), data.maxHealth(), data.stamina(), data.maxStamina(), data.mana(), data.maxMana()),
                    left + 12, top + 166, 0xA8D8FF);
        }
        super.render(graphics, mouseX, mouseY, partialTick);
    }
}
