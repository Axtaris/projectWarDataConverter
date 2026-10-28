# Enhancements structured from their text

- Adeptus Custod / AQUILAN SHIELD / **Not a Shell Wasted**: Adeptus Custodes Infantry model only. This unit’s ranged attacks have +1 A.
  - [{"Value": "1", "Type": "Add", "Target": "Attacks", "WeaponScope": "Ranged", "Scope": "Unit"}]
- Adeptus Custod / AURIC CHAMPIONS / **Shroud of the Hidden Blade**: Adeptus Custodes model only. This model has:
Stealth Lone Operative.
  - [{"Target": "CoreAbilities", "Type": "Add", "Values": ["Stealth"]}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Lone Operative"]}]
- Adeptus Custod / MIGHT OF THE MORITOI / **Memento Moritoi (one per army) (Upgrade)**: Adeptus Custodes Dreadnought model only. This model’s melee attacks have +1 A, S and D.
  - [{"Value": "1", "Type": "Add", "Target": "Attacks", "WeaponScope": "Melee"}, {"Value": "1", "Type": "Add", "Target": "Strength", "WeaponScope": "Melee"}, {"Value": "1", "Type": "Add", "Target": "Damage", "WeaponScope": "Melee"}]
- Adeptus Mechan / RAD-ZONE CORPS / **Malphonic Susurrus**: Adeptus Mechanicus model only. While the bearer is leading a unit, models in that unit have the Stealth ability.
  - [{"Target": "CoreAbilities", "Type": "Add", "Scope": "Unit", "Values": ["Stealth"]}, {"Target": "CoreAbilities", "Type": "Add", "Scope": "AttachedUnit", "Values": ["Stealth"]}]
- Aeldari.json / GHOSTS OF THE WEBWAY / **Mistweave**: Shadowseer model only. While the bearer is leading a unit, models in that unit have the Infiltrators ability.
  - [{"Target": "CoreAbilities", "Type": "Add", "Scope": "Unit", "Values": ["Infiltrators"]}, {"Target": "CoreAbilities", "Type": "Add", "Scope": "AttachedUnit", "Values": ["Infiltrators"]}]
- Black Templars / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Black Templars / VOW-SWORN CRUSADERS / **Consecrating Aura**: Adeptus Astartes model only. This unit has 5+ InSv.
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Black Templars / VOW-SWORN CRUSADERS / **Incendiary Animus**: Chaplain/Judiciar model only. This unit’s melee attacks have +1 S.
  - [{"Value": "1", "Type": "Add", "Target": "Strength", "WeaponScope": "Melee", "Scope": "Unit"}]
- Blood Angels.j / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Blood Angels.j / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Dark Angels.js / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Dark Angels.js / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Deathwatch.jso / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Deathwatch.jso / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Imperial Fists / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Imperial Fists / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Imperial Fists / MEDUSA'S WRATH / **The Flesh is Weak**: Adeptus Astartes model only. This model:
Has +1 T. Has Feel No Pain 5+.
  - [{"Target": "Toughness", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Iron Hands.jso / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Iron Hands.jso / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Iron Hands.jso / MEDUSA'S WRATH / **The Flesh is Weak**: Adeptus Astartes model only. This model:
Has +1 T. Has Feel No Pain 5+.
  - [{"Target": "Toughness", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Necrons.json / AWAKENED DYNASTY / **Nether-realm Casket**: Necrons model only. While the bearer is leading a unit, models in that unit have the Stealth ability.
  - [{"Target": "CoreAbilities", "Type": "Add", "Scope": "Unit", "Values": ["Stealth"]}, {"Target": "CoreAbilities", "Type": "Add", "Scope": "AttachedUnit", "Values": ["Stealth"]}]
- Orks.json / BRUTE BOSSES / **Brutal But Kunnin’**: Warboss model only. This model’s melee attacks have +1 D.
  - [{"Value": "1", "Type": "Add", "Target": "Damage", "WeaponScope": "Melee"}]
- Orks.json / GREEN TIDE / **'Ardboyz (Upgrade)**: Boyz unit only. This unit has 4+ Sv.
  - [{"Target": "Save", "Value": "4+", "Scope": "Unit"}]
- Raven Guard.js / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Raven Guard.js / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Raven Guard.js / MEDUSA'S WRATH / **The Flesh is Weak**: Adeptus Astartes model only. This model:
Has +1 T. Has Feel No Pain 5+.
  - [{"Target": "Toughness", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Salamanders.js / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Salamanders.js / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Salamanders.js / MEDUSA'S WRATH / **The Flesh is Weak**: Adeptus Astartes model only. This model:
Has +1 T. Has Feel No Pain 5+.
  - [{"Target": "Toughness", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Space Marines. / BLADE OF ULTRAMAR / **Armour of Antoninus**: Adeptus Astartes model only. This model has:
2+ Sv. Feel No Pain 5+.
  - [{"Target": "Save", "Value": "2+"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Space Marines. / FORGEFATHER’S SEEKERS / **Immolator**: Adeptus Astartes model only. This unit’s [TORRENT] weapons have +1 A.
  - [{"Value": "1", "Type": "Add", "Target": "Attacks", "WeaponScope": "Ranged", "IncludedKeywords": ["TORRENT"], "Scope": "Unit"}]
- Space Marines. / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Space Marines. / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Space Marines. / MEDUSA'S WRATH / **The Flesh is Weak**: Adeptus Astartes model only. This model:
Has +1 T. Has Feel No Pain 5+.
  - [{"Target": "Toughness", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Space Marines. / SHADOWMARK TALON / **Umbral Raptor**: Adeptus Astartes infantry model only. This model has:
Fights First. Lone Operative.
  - [{"Target": "CoreAbilities", "Type": "Add", "Values": ["Fights First"]}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Lone Operative"]}]
- Space Marines. / SPEARPOINT TASK FORCE / **Hunter’s Eye**: Adeptus Astartes model only. This unit’s ranged attacks:
Have [IGNORES COVER]. Have [SUSTAINED HITS 1].
  - [{"Value": "IGNORES COVER", "Type": "Add", "Target": "Keywords", "WeaponScope": "Ranged", "Scope": "Unit"}, {"Value": "SUSTAINED HITS 1", "Type": "Add", "Target": "Keywords", "WeaponScope": "Ranged", "Scope": "Unit"}]
- Space Wolves.j / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Space Wolves.j / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Ultramarines.j / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- Ultramarines.j / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- Ultramarines.j / MEDUSA'S WRATH / **The Flesh is Weak**: Adeptus Astartes model only. This model:
Has +1 T. Has Feel No Pain 5+.
  - [{"Target": "Toughness", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- White Scars.js / GLADIUS TASK FORCE / **Standard of the Emperor Ascendant**: Ancient model only. This model has:
+1 OC and Ld. Feel No Pain 5+. The following ability:
Ancient Exhortation (Once per battle, per army): When this u
  - [{"Target": "OC", "Type": "Add", "Value": "1"}, {"Target": "Leadership", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
- White Scars.js / IRONSTORM SPEARHEAD / **Redoubtable Machine Spirit (Upgrade)**: Adeptus Astartes Vehicle unit only (excluding Dedicated Transport/Fly/Walker units). This unit:
Has 5+ InSv. At the end of your Command phase, heals 1
  - [{"Target": "InvulSave", "Value": "5+", "Scope": "Unit"}]
- White Scars.js / MEDUSA'S WRATH / **The Flesh is Weak**: Adeptus Astartes model only. This model:
Has +1 T. Has Feel No Pain 5+.
  - [{"Target": "Toughness", "Type": "Add", "Value": "1"}, {"Target": "CoreAbilities", "Type": "Add", "Values": ["Feel No Pain 5+"]}]
