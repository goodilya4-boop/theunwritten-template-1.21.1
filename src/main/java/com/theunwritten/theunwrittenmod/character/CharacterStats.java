package com.theunwritten.theunwrittenmod.character;

/** Direct implementation of the continuous test formulas in character-model specification v1.0. */
public record CharacterStats(double physicalForce, double speed, double reaction, double coordination,
                             double bodyDurability, double maxHealth, double maxStamina,
                             double maxMana, double willpower) {
    public static CharacterStats calculate(CharacterData c) {
        double s=c.strength()/10.0, d=c.dexterity()/10.0, t=c.constitution()/10.0;
        double i=c.intelligence()/10.0, w=c.wisdom()/10.0, h=c.charisma()/10.0;
        return new CharacterStats(
                10*Math.pow(s,.9)*Math.pow(t,.1),
                10*Math.pow(d,.8)*Math.pow(s,.2),
                10*Math.pow(d,.7)*Math.pow(w,.3),
                10*Math.pow(d,.85)*Math.pow(w,.15),
                10*Math.pow(t,.9)*Math.pow(s,.1),
                100*Math.pow(t,.9),
                100*Math.pow(t,.8)*Math.pow(w,.2),
                100*Math.pow(i,.5)*Math.pow(w,.5),
                10*Math.pow(w,.7)*Math.pow(h,.3));
    }
}
