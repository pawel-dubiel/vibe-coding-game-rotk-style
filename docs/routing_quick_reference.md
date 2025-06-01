# Routing System - Quick Reference

## 📊 Key Thresholds

| Condition | Morale % | Effect |
|-----------|----------|--------|
| **Automatic Routing** | < 20% | Unit immediately starts routing |
| **Probability Routing** | 20-40% | Chance to route based on morale |
| **Rally Threshold** | ≥ 40% | Can attempt to rally and stop routing |
| **Zone of Control** | ≥ 25% | Can exert ZOC on enemies |

## ⚔️ Morale Loss Sources

| Source | Morale Loss | Notes |
|--------|-------------|-------|
| **Casualties** | Up to -30 | Based on % soldiers lost |
| **Rear Attack** | -15 | High routing chance (40-60%) |
| **Flank Attack** | -10 | Moderate routing chance (15-30%) |
| **Front Attack** | -5 | Standard penalty |
| **Multiple Attacks** | -5 per extra | Progressive fatigue penalty |
| **Cavalry Charge** | -15 to -30 | Depends on charge type |

## 🏃 Routing Effects

### ✅ Advantages (for routing unit)
- **-30% damage taken** (scattered formation)
- **Can move through enemy ZOC** (fleeing)
- **Automatic flee movement** (immediately when routing starts)

### ❌ Disadvantages
- **No Zone of Control** (cannot threaten enemies)
- **Forced movement away from enemies** (automatic)
- **Cannot perform most actions** (routing panic)

## 🛡️ Rally Mechanics

### Automatic Rally (End of Turn)
```
Base Chance: 70%
High Morale (≥60%): 90%
Heavy Damage (<50% soldiers): 60% of base
Minimum Morale Required: 40%
```

### Manual Rally (General Ability)
```
Morale Restored: +30
Will Cost: 20
Cooldown: 3 turns
Range: 2 hexes
Effect: Immediately stops routing
```

## 🎯 Tactical Tips

### Preventing Routing
1. **Keep morale ≥40%** - Safe zone for most units
2. **Protect flanks and rear** - Face enemies when possible
3. **Use terrain** - Hills/forests provide defensive bonuses
4. **General support** - Inspire and Rally abilities

### Exploiting Enemy Routing
1. **Target low morale units** (< 50% morale)
2. **Flank attacks** for bonus routing chance
3. **Chain reactions** - One routing unit can trigger others
4. **Pursue routing units** - They can't fight back effectively

### Recovery Strategies
1. **Pull back routing units** - Get them to safety
2. **General Rally ability** - Instant morale boost
3. **End turn quickly** - Automatic rally attempts
4. **Screen with reserves** - Protect while rallying

## 🎮 Visual Indicators

| Icon | Meaning |
|------|---------|
| 🏳️ White Flag | Unit is routing |
| "ROUTING!" | Status text in unit info |
| Red morale bar | Low morale (< 25%) |
| Yellow morale bar | Wavering (25-50%) |

## ⚡ Quick Reactions

### When Your Unit Routes
1. 🏃 **Unit automatically flees** (immediate when routing starts)
2. ✅ **End turn to attempt rally**
3. ✅ **Use Rally ability if available**
4. ✅ **Screen with other units**

### When Enemy Routes
1. ✅ **Pursue if safe** (routing units are vulnerable)
2. ✅ **Target nearby enemies** (morale chain reaction)
3. ✅ **Exploit gaps** in enemy line
4. ✅ **Prevent rally** with continued pressure

## 🧠 AI Behavior

- **Prioritizes low morale targets** (+75 attack value)
- **Seeks rear/flank attacks** (+25-50 attack value)
- **Treats routing units as minimal threat** (-70% threat value)
- **Exploits routing gaps** in defensive lines

---

*For complete details, see [routing_mechanism.md](routing_mechanism.md)*