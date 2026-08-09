# Analyse der SHA-256-Kompressionsfunktion unter Bitcoin-Randbedingungen

**Arbeitsdokument, Stand 9. August 2026**
*Ergänzt um Abschnitt 18 (Rückwärtsrechnung), Abschnitt 19 (Nachprüfung),
Abschnitt 20 (Fortschrittskurve für K1(r)) und Abschnitt 21 (Neutrale Bits
bei r = 17). Korrekturen aus der Nachprüfung sind an Ort und Stelle
eingetragen und in 19.2 aufgeführt.*

Untersuchungsgegenstand: SHA-256 auf 32-Byte-Eingabe (hier **K1** genannt) —
identisch mit dem zweiten Durchlauf des Bitcoin-Double-Hash — sowie mehrere
eingeschränkte Varianten. Die Notation ist in Abschnitt 0 festgelegt.
Alle Zahlen in diesem Dokument sind gerechnet, nicht geschätzt. Die zugehörigen
Programme liegen im Anhang.

---

## 0. Notation und Definitionen

### 0.1 Untersuchte Funktionen

| Symbol | Definition |
|---|---|
| **F** | SHA-256-Kompressionsfunktion in Grundform: freier 512-Bit-Block (W₀–W₁₅ alle frei), fester IV nach FIPS 180-4. Dient als Vergleichsmaßstab. |
| **K0** | Zweiter Block des **ersten** SHA-256-Durchlaufs über den 80-Byte-Header. Midstate aus Block 1 fest; freie Eingabe: die 4 Nonce-Byte in W₃, also 2³² Eingaben. Das eigentlich Bitcoin-spezifische Objekt. |
| **K1** | SHA-256 auf exakt 32 Byte Eingabe. Ein einziger Block; das Padding ist dadurch festgelegt (W₈–W₁₅ konstant), frei sind W₀–W₇ (256 Bit). **Identisch mit dem zweiten Durchlauf des Bitcoin-Double-Hash.** |
| **K1-R** | K1 mit der relationalen Bedingung W₀ ≡ −σ₀(W₁) mod 2³². Sieben freie Wörter (224 Bit); erzwingt W₁₆ = 0. |
| **K1-1** | K1 mit Byte 0–29 auf Null. 16 freie Bits, 65.536 Eingaben — erschöpfend analysierbar. |
| **K1-1[p]** | K1-1 mit Füllbyte p statt 0x00, p ∈ {0x00, 0xFF, 0xAA, 0x55, 0x0F}. K1-1 = K1-1[0x00]. |

**Wichtig:** „SHA-256 mit 256-Bit-Eingabe" und „zweiter Durchlauf des
Double-Hash" bezeichnen dasselbe Objekt — nämlich K1. Eine 32-Byte-Nachricht
ergibt genau einen Block mit festgelegtem Padding. Ein separater Name wäre
redundant.

### 0.2 Varianten und Implementierungen

| Notation | Bedeutung |
|---|---|
| **K1⟨r⟩** | auf r Runden reduziert, z. B. K1⟨16⟩. Ohne Angabe: 64 Runden. |
| **K1^std** | Lehrbuch-Implementierung, 952 Wortoperationen |
| **K1^spez** | spezialisiert durch Konstantenfaltung, 861 Operationen |
| **K1^aig** | And-Inverter-Graph, 198.167 Gatter |
| **K1^xaig** | XAIG mit nativen XOR-Knoten, 98.899 Gatter |

Die Hochgestellten bezeichnen **Implementierungen derselben Funktion**. Alle
sind bitidentisch (Satz 7); sie unterscheiden sich nur im Aufwand.

### 0.3 Weitere Begriffe

| Begriff | Definition |
|---|---|
| **gültig** | Bei K1-1: Ausgabe mit ≥ 10 führenden Nullbits. Ergibt 81 der 65.536 Werte. |
| **Kostenmetrik** | Wortoperationen, AIG-Gatter oder XAIG-Gatter. Minimalitätsaussagen gelten stets nur relativ zu einer Metrik (siehe 9.2). |

Methodischer Grundsatz für alle Messungen: **Jede Messung mit Kontrollgruppe.**
Ohne Vergleich gegen Zufallsdaten oder Zufallskonstanten ist ein Messwert nicht
interpretierbar.

---

## 1. Bewiesene Sätze

Diese Aussagen sind exakt, nicht statistisch.

**Satz 1 (Padding).** Für Eingabelänge 256 Bit gilt W₈ = 0x80000000,
W₉…W₁₄ = 0, W₁₅ = 0x00000100.
*Beweis: Definition des SHA-256-Paddings. Verifiziert.*

**Satz 2 (Nullstelle W₁₆, Variante K1-R).** Unter der Bedingung
W₀ ≡ −σ₀(W₁) mod 2³² gilt W₁₆ = 0 — und ausschließlich W₁₆.
*Beweis: W₁₆ = σ₁(W₁₄) + W₉ + σ₀(W₁) + W₀; mit W₁₄ = W₉ = 0 und σ₁(0) = 0 folgt
W₁₆ = σ₀(W₁) + W₀ = 0. Verifiziert in 2000/2000 Zufallsfällen.*

**Satz 3 (Davies-Meyer-Inversion).** Unter H = 0 gilt State₆₄⁽ⁱ⁾ ≡ ~IVᵢ + 1 mod 2³².

| Register | IV | State₆₄ |
|---|---|---|
| A | 0x6a09e667 | 0x95f61999 |
| B | 0xbb67ae85 | 0x4498517b |
| C | 0x3c6ef372 | 0xc3910c8e |
| D | 0xa54ff53a | 0x5ab00ac6 |
| E | 0x510e527f | 0xaef1ad81 |
| F | 0x9b05688c | 0x64fa9774 |
| G | 0x1f83d9ab | 0xe07c2655 |
| H | 0x5be0cd19 | 0xa41f32e7 |

*Beweis: Modulare Arithmetik. Alle acht Werte verifiziert.*

**Satz 4 (Runde 0 von K1).** a₁ = W₀ + 0xfc08884d und e₁ = W₀ + 0x98c7e2a2,
beide affin in W₀.
*Beweis: Alle übrigen Operanden sind IV-Konstanten.*

**Satz 5 (Ch/Maj in Runde 1).** Genau 15 der 32 Ch-Bits und 17 der 32 Maj-Bits
sind determiniert.
*Beweis: f, g bzw. b, c sind noch IV-Konstanten. Bit i ist fest, wo sie
übereinstimmen. Diese Determiniertheit existiert ausschließlich in Runde 1 —
ab Runde 2 ist je ein Operand variabel, ab Runde 3 beide.*

**Satz 6 (K1-1, Runden 0–6).** Der Zustand ist konstant und
eingabeunabhängig.
*Beweis: Die freien Bits liegen in W₇; Runden 0–6 verarbeiten W₀…W₆ = 0.*

**Satz 7 (Obere Schranke).** Für die Berechnung von H₇ genügen **861 von 952**
Operationen bei K1 und **747** bei K1-1.
*Beweis: konstruktiv, durch maschinelle Dead-Code-Elimination auf dem
vollständigen Operationsgraphen.*

**Satz 8 (Ausgangskegel).** Die Runden 61–63 sind für H₇ irrelevant.
*Beweis: h₆₄ = g₆₃ = f₆₂ = e₆₁ — reine Registershifts. Verifiziert an 3000
Zufallseingaben.*
*Einordnung: kein eigener Fund. Dieser Early-Exit ist im Mining-ASIC-Design
etabliert und wird dort seit Jahren genutzt; die Messung reproduziert ihn nur
und quantifiziert die Kegeltiefe auf 5 Runden.*

**Satz 9 (Algebraischer Grad, K1-1).** Die Ausgabebits haben algebraischen
Grad 15–16 bei 32.343–33.093 ANF-Monomen, im Mittel 32.765,7.
*Beweis: Möbius-Transformation über alle 2¹⁶ Eingaben — erschöpfend.
Erwartungswert für eine Zufallsfunktion: 32.768 Monome, Grad 16.*
*Präzisierung (Nachprüfung 19.1).* Frühere Fassungen nannten den Bereich
32.540–32.840. Dieser Wert stammt aus **sechs Stichprobenbits** (0, 7, 63, 127,
200, 255), nicht aus allen 256 Ausgabebits; `k1_1_formel.py` misst genau diese
sechs. Die Stichprobe ist exakt reproduziert (Bit 0 → 32.540, Bit 255 → 32.840).
Über alle 256 Bits ist der Bereich weiter: **32.343–33.093 bei Mittel 32.765,7**,
weiterhin auf Zufallsniveau (Erwartung 32.768). Die Aussage des Satzes ändert
sich nicht, ihr Geltungsbereich schon.

**Satz 10 (Abzählschranke).** Fast alle Funktionen mit 81 Mintermen aus 65.536
benötigen ≥ 60 Gatter.
*Beweis: Shannon-Abzählung. 2⁸⁹⁵ solcher Funktionen gegen ((16+g)²·16)^g
Schaltungen.*

**Satz 11 (Affine Inäquivalenz).** Die K1-1-Ausgabefunktionen verschiedener
Varianten K1-1[p] für p ∈ {0x00, 0xFF, 0xAA, 0x55, 0x0F} sind paarweise **nicht**
affin äquivalent.
*Beweis: Die Nichtlinearität ist eine affine Invariante. Gemessen — die Werte
sind paarweise verschieden, damit ist für jedes Paar ausgeschlossen, dass eine
affine Transformation existiert:*

| p | 0x00 | 0xFF | 0xAA | 0x55 | 0x0F |
|---|---|---|---|---|---|
| Nichtlinearität | 1924 | 1929 | 1925 | 1931 | 1927 |

*Zusätzlich: 5001 Bit-Permutationen geprüft, null Treffer.*
*Zwei Präzisierungen (Nachprüfung 19.1):* Frühere Fassungen listeten die Werte
aufsteigend sortiert (1924, 1925, 1927, 1929, 1931) in der Reihenfolge der
p-Liste, was eine falsche Zuordnung nahelegte. Die Wertemenge ist unverändert,
die Zuordnung steht oben. Ferner wird die Nichtlinearität in `k1_transform.py`
auf einer **12-Bit-Restriktion** gemessen (NB = 12, also 4096 Eingaben), nicht
auf vollem K1-1; die Maximalnichtlinearität dieses Raums liegt bei 2048.

---

## 2. Strukturkarte von K1

Wo im Algorithmus liegt überhaupt nutzbare Struktur?

| Bereich | Befund |
|---|---|
| Runde 0 | vollständig vorberechenbar, affin in W₀ |
| Runde 1 | 15/32 Ch-Bits, 17/32 Maj-Bits determiniert |
| Runden 2–3 | Determiniertheit zerfällt: 192 → 128 → 64 Bit |
| **Ab Runde 4** | **exakt 0 determinierte Bits** |
| Runden 8–15 | K[t]+W[t] vorfaltbar (Padding konstant) |
| Runden 16–60 | keine Struktur |
| Runden 61–63 | für H₇ irrelevant (Kegel-Tiefe 5) |

**Algebraischer Grad pro Runde** (Cube-Summen, 800 Cubes):

| Runde | Grad ≥2 | Grad ≥3 | Grad ≥4 |
|---|---|---|---|
| 1–2 | 0 | 0 | 0 |
| 3 | 102 | 0 | 0 |
| 5 | — | — | 175 |
| 8 | 251 | 249 | 201 |

Runde 2 ist vollständig affin. Ab Runde 5 sättigt der Grad.

**Lawineneffekt:** Ein gekipptes Nonce-Bit erzeugt ab Runde 4 Divergenz und
ab Runde ~10 die vollen ~50 % Zustandsunterschied.

---

## 3. Optimierung: verifizierte Ergebnisse

**Spezialisierte K1-Form:** 861 statt 952 Operationen (−9,6 %), maschinell als
Optimum aller semantikerhaltenden Kürzungen nachgewiesen. Bitidentisch zur
vollen Funktion, verifiziert an 3000 Zufallseingaben.

**K1-1:** 747 Operationen (−21,5 %).

| Variante | freie Wörter | nötige Ops | Ersparnis |
|---|---|---|---|
| K1 | 8 | 861 | 9,6 % |
| 16 Byte genullt | 4 | 799 | 16,1 % |
| 24 Byte genullt | 2 | 765 | 19,6 % |
| K1-1 (30 Byte) | 1 | 747 | 21,5 % |

**Fitness-Auswertung 15,8× beschleunigt** bei bitidentischem Ergebnis
(Differenz 0,00e+00 in allen Prüfungen). Zwei Kernideen: Lauflänge via
Count-Leading-Zeros statt Bitmatrix-Schleife; Positionsgewichte via
16-Bit-Lookup-Tabellen.

---

## 4. Widerlegte Ansätze

Jeder Punkt mit Kontrollgruppe geprüft.

### 4.1 Kürzeste Formel für die 81 gültigen Werte

| Verfahren | Ergebnis | Kontrolle |
|---|---|---|
| ANF (exakt) | 32.540 Monome, Grad 16 | Zufallsfunktion: 32.768 |
| zlib-Kompression | 100,0 % (keine Kompression) | — |
| SOP-Logikminimierung | 78 Terme, 15,96 Literale/Term | Zufall: 80,2 Terme |
| Genetische Programmierung | MCC 0,017 | „immer nein": MCC 0,0 |
| Arithmetische Ausdrücke | 1/81 Treffer | Zufallspaare: 0/81 |
| Registermaschine (11 CPU-Ops) | 60/81 richtig, 32.708 falsch | — |

Von 78 Cubes der Logikminimierung decken **75 genau einen** Wert — die minimale
Schaltung ist faktisch eine Tabelle.

**Wichtige Einschränkung:** ANF-Monomzahl ist *nicht* die minimale Schaltungsgröße.
Eine Schaltung darf Teilergebnisse wiederverwenden, eine Normalform nicht. Die
Aussage „kürzeste Formel hat 32.768 Terme" war falsch; korrekt ist: obere
Schranke 747 Operationen, untere Schranke unbekannt (Bereich 60–747 offen).

### 4.2 Filterung / Early Reject

Systematisch getestet: Kompression des Zwischenzustands nach Runden 7, 9, 12, 16
mit sechs verschiedenen Operationen.

**Ergebnis:** In jeder Runde und bei jeder Kompression entspricht die Zahl
falsch durchgelassener Werte exakt der Zufallserwartung 65455 · min(81,B)/B.

Beispiel Runde 9: „unterste 12 Bit von e" lässt 1268 durch, statistisch
erwartet 1294.

**Kern:** Filtern setzt Sortierung voraus. Eine Kompression auf B Werte kann
höchstens B Gruppen unterscheiden; bei zufällig verteilten gültigen Werten
schleppt jede Gruppe proportional viele ungültige mit. Der Filtergewinn ist
exakt gleich dem Informationsverlust.

### 4.3 Übertragbarkeit zwischen den Varianten K1-1[p]

Die in Bereich A gefundene Funktion, getestet auf anderen Bereichen:

| getestet auf | MCC |
|---|---|
| A (Heimatbereich) | 0,0733 |
| B | −0,0008 |
| C | −0,0007 |
| D | −0,0008 |

Keine Übertragbarkeit. Konsistent mit Satz 11 (affine Inäquivalenz).

### 4.4 Der Kapazitätsbefund

Historische Beobachtung (>70 % Trefferquote bei GP, Zusammenbruch beim
Bereichswechsel) ist vollständig durch Modellkapazität erklärt:

Ein GA mit 21 Instruktionen aus dem verwendeten Suchraum hat log₂(F) ≈ **367 Bit**
Kapazität. Zum Auswendiglernen von 81 Labels nötig: 81 Bit. Die hohe Trefferquote
war garantiert — auch bei vollständig zufälligen Labels.

**Empirisch bestätigt:** Dieselbe Suche auf Zufalls-Labels erreichte 2–3 Treffer,
auf echten Daten 2 Treffer. Kein Unterschied.

**Konvergenzkurve (Population 2000, ephemere Batches):**

| Gen | Train | TEST |
|---|---|---|
| 0 | 0,300873 | 0,300530 |
| 12 | 0,301053 | 0,300516 |
| 34 | 0,301232 | 0,300447 |

Train steigt, TEST fällt — Overfitting in Reinform.

### 4.5 Die relationale Bedingung (Variante K1-R)

Die aus dem Ausgangskonzept stammende Bedingung W₀ ≡ −σ₀(W₁) mod 2³² sollte
durch Konstantenauslöschung vereinfachen. Gemessene Wirkung:

| Kriterium | Ergebnis |
|---|---|
| konstant propagierte Wörter | **nur W₁₆** — die Kaskade endet nach einem Wort |
| determinierte Bits in W₁₇–W₃₁ | 0 |
| Kosten | −32 Bit Suchraum (W₀ vollständig durch W₁ festgelegt) |
| Klauselersparnis im SMT-Modell | 1344 → 448 für W₁₈, global < 2 % |

**Bilanz negativ.** Unter der Zielbedingung H = 0 sinkt die erwartete
Lösungszahl von 1 (bei K1) auf 2⁻³² (bei K1-R) — die Bedingung entfernt genau
die Freiheitsgrade, die für eine Lösung nötig wären. Ein UNSAT-Ergebnis für
K1-R wäre daher kein kryptanalytischer Befund, sondern reine Abzählung.

### 4.6 Fester Zielhash statt Target-Bereich

| | Versuche | Netzwerk (932 EH/s) |
|---|---|---|
| Normales Mining | 2⁷⁹ | 10,8 Minuten |
| Fester Zielhash | 2²⁵⁶ | 3,9 × 10⁴⁸ Jahre |

Faktor 2¹⁷⁷. Urbilder existieren zwar (~4100 im erreichbaren Suchraum von 2²⁶⁸),
sind aber nicht auffindbar.

### 4.7 Blockchain als Datenquelle

Analyse der 10 niedrigsten Block-Hashes der Historie (Quelle: BitMEX Research, Stand Block 720.441):

- Rekord: Block 634.842, 15.06.2020, Binance Pool, **94 führende Nullbits**
  (23 Hex-Nullen), einziger Block mit 23 Hex-Nullen
- Abstand zu H = 0: Faktor 2¹⁶² ≈ 5,8 × 10⁴⁸
- Bits nach den führenden Nullen: 839 Einsen von 1653, erwartet 826 ± 20
  → **0,61 Sigma**, unauffällig
- Häufigkeitsverteilung: jede zusätzliche Hex-Null teilt die Anzahl durch
  ~16 (gemessen 14,9 / 15,9 / 18,5 / 32,0), wie für Zufall erwartet

Der 19er-Ausreißer (Faktor 0,9) ist durch die Difficulty-Verschiebungen der
Epochen erklärt (Simpson-Paradoxon), nicht durch SHA-256.

---

## 5. Konstantenanalyse

Die einzige Messreihe des Tages, die einen Effekt über der Kontrollgruppe zeigt.

**Methode:** Rotationssymmetrie-Test. Gemessen wird die Bit-Übereinstimmung
zwischen F(rotl(M,r)) und rotl(F(M),r), gemittelt über Rotationsweiten
1, 3, 7, 11. 50 % = Symmetrie vollständig gebrochen (Optimum).

**Positivkontrolle:** Mit K = 0 und IV = 0 ist SHA-256 in Runde 1 zu **100 %**
rotationssymmetrisch. Der Test erkennt Symmetrie also zuverlässig — anders als
Lawineneffekt oder Bit-Bias, bei denen die degenerierte Variante nicht auffiel.

**Ergebnis (Grundform F, 40 Zufallssätze):**

| Konstantensatz | z-Werte (Runde 1–4) | Mittel |
|---|---|---|
| **Echt (Kubikwurzeln Primzahlen)** | −0,09 −0,14 +0,13 −0,05 | **−0,04** |
| Quadratwurzeln Primzahlen | −2,71 −2,83 −2,83 −2,45 | **−2,70** |
| √2 | −2,71 −2,81 −2,68 −2,60 | −2,70 |
| Pi | −0,42 −0,20 −0,38 −0,23 | −0,31 |
| e | −0,79 −0,76 −1,29 −0,91 | −0,94 |
| √3 | +0,49 +0,45 +0,65 +0,39 | +0,49 |
| Goldener Schnitt | −0,05 +0,13 +0,41 −0,07 | +0,11 |
| Fibonacci | +8,15 +9,08 +9,12 +9,01 | **+9,09** |

**Befunde:**

1. Die echten SHA-256-Konstanten liegen bei z = −0,04, also exakt auf
   Zufallsniveau. **Kein Hinweis auf absichtliche Schwächung.**
2. Quadratwurzeln scheinen die Symmetrie besser zu brechen (−2,70). Der Effekt
   überlebt zwar den Methodenwechsel Dezimal↔Binär, erweist sich in der
   Kausalanalyse (Abschnitt 5.1) aber als Artefakt zweier Messfehler.
3. Fibonacci fällt mit z ≈ +9 klar durch — der Test ist also empfindlich genug,
   um schlechte Konstantenwahl zu erkennen.

**In K1-1 löst sich der Effekt auf:** Kubikwurzeln z = −0,02, mittlerer Rang
23,3 von 50 Zufallssätzen (Erwartung 25).

### 5.1 Kausalanalyse: der Quadratwurzel-Befund ist ein Artefakt

Der oben berichtete Wert z = −2,70 hat **zwei** methodische Ursachen, beide
durch eine hochpräzise Nachmessung aufgeklärt.

**Messaufbau der Nachmessung.** Vektorisiert, mit deutlich verdichteter
Abtastung:

| Parameter | Wert |
|---|---|
| Nachrichten je Rotationsweite | 6.000 |
| Rotationsweiten | 8 (alle zu 32 teilerfremden: 1,3,5,7,9,11,13,15) |
| verglichene Bits je Messpunkt | **12.288.000** |
| Standardfehler je Messpunkt | 0,0143 % |
| 95-%-Konfidenzintervall | ± 0,0280 % |
| Zufallsbaseline | **100** unabhängige Konstantensätze |

**Ursache 1 — Wertüberlappung zwischen IV und K.** In der ursprünglichen
Messung war der IV stets √p. „Quadratwurzeln" bedeutete daher K = √p bei
IV = √p, mithin K₀…K₇ = IV₀…IV₇ — acht identische Werte.

Gestaffelter Test der Überlappung:

| gemeinsame Werte | Runde 1 | Runde 2 | Runde 3 | Runde 4 |
|---|---|---|---|---|
| **0** | 88,6149 % | 76,1827 % | 63,6880 % | 51,2074 % |
| 1 | 85,9883 % | 73,4932 % | 60,9903 % | 48,4853 % |
| 2 | 85,9981 % | 73,5174 % | 61,0216 % | 48,5066 % |
| 4 | 85,9957 % | 73,5210 % | 61,0149 % | 48,5392 % |
| 8 | 85,9894 % | 73,5260 % | 61,0220 % | 48,5029 % |

**Der Effekt ist nicht monoton.** Der gesamte Sprung liegt zwischen null und
*einem* gemeinsamen Wert; die Überlappungen 1, 2, 4 und 8 sind untereinander
ununterscheidbar (Differenzen < 0,04 %, also unter dem Konfidenzintervall).

Es handelt sich also um einen **Einzelwert-Effekt**: Sobald K₀ = IV₀ gilt,
addiert Runde 0 eine Konstante, die bereits im Zustand steht. Die weiteren
sieben Übereinstimmungen wirken nicht mehr, weil sie auf bereits veränderten
Zustand treffen.

**Ursache 2 — zu kurzer Mittelungsbereich.** Der Effekt existiert
ausschließlich in den Runden 1–4 und verschwindet ab Runde 5 vollständig. Der
ursprünglich berichtete Mittelwert umfasste genau diese vier Runden.

**Gesamtvergleich, sechs Kandidaten, Mittel über die Runden 1–8:**

| Konstantensatz | z |
|---|---|
| **A — FIPS: IV = √p, K = ∛p** | **+0,455** |
| B — homogen √p, 8-fach überlappt | −2,724 |
| B* — homogen √p, disjunkte Primzahlen | +1,987 |
| C — homogen ∛p, disjunkte Primzahlen | −0,864 |
| D — Pi-Nachkommastellen | −0,279 |
| E — ∛p anderer Primzahlen (p₁₀₀…p₁₆₃) | −0,188 |

**Differenz B gegen B\*: 4,71 Sigma** — allein durch die Wertüberlappung, bei
sonst identischer Konstruktionsvorschrift.

### 5.2 Bewertung der Hintertür-Hypothese

Die Messreihe erlaubt eine belastbare Aussage, weil der Test seine
Empfindlichkeit nachweist:

1. **Der Test erkennt schlechte Konstantenwahl.** Fibonacci fällt mit z ≈ +9
   durch, die Überlappungsvariante mit 4,71 Sigma Differenz. Das Verfahren ist
   also nicht blind.
2. **Die tatsächlich verwendeten FIPS-Konstanten liegen bei z = +0,455** —
   innerhalb des Zufallsbereichs, bei einer Baseline aus 100 Sätzen.
3. **Die Kombination √p für den IV und ∛p für Kₜ vermeidet die Überlappung
   strukturell.** Wären beide aus derselben Wurzelklasse gebildet, entstünde
   der messbare Effekt.
4. **Vier voneinander unabhängige Alternativsätze** (Pi, andere Primzahlen,
   homogen kubisch, disjunkt quadratisch) liegen ebenfalls im Zufallsbereich.
   Es gibt also keine naheliegende Wahl, die deutlich besser wäre.

**Schlussfolgerung:** Für die Hypothese einer absichtlich geschwächten
Konstantenwahl in SHA-256 findet sich in dieser Messreihe kein Anhaltspunkt.
Der einzige Satz mit signifikanter Abweichung ist einer, den SHA-256 gerade
**nicht** verwendet.

---

## 6. Restsymmetrie in K1-1

K1-1 bricht die Rotationssymmetrie **schwächer** als K1:

| Runden | K1-1 | K1 | Differenz |
|---|---|---|---|
| 1 | 88,48 % | 87,55 % | +0,93 % |
| 4 | 51,37 % | 50,10 % | +1,27 % |
| 8 | 52,23 % | 49,87 % | +2,36 % |
| 12 | 50,19 % | 49,94 % | +0,25 % |

Ursache: rotierte Nullen bleiben Nullen — es gibt weniger Material, an dem die
Symmetrie brechen könnte. Das ist eine Schwächung *der Einschränkung*, nicht
von SHA-256.

**Trägt die Restsymmetrie?** Erschöpfende Suche nach Rotationskollisionen über
alle 65.536 Eingaben:

| Runden | Treffer (k=16 Bit) | erwartet | Treffer (k=24 Bit) |
|---|---|---|---|
| 4–8 | 0 | 1,0 | 0 |
| 12 | 4 | 1,0 | 0 |
| 16 | 1 | 0,33 | 0 |
| 20 | 0 | 0,33 | 0 |

Bei k = 24 Bit null Treffer in jeder Runde. Die 4 bei Runde 12 liegen bei
21 durchgeführten Tests im Erwartungsbereich (Poisson, p ≈ 1,5 %).

**Die 52 % waren eine statistische Restkorrelation über viele Bits, keine
verwertbare Kollision.**

---

## 7. Äquivalente Umformungen der Rundenfunktion

Alle Aussagen dieses Abschnitts sind bitidentisch verifiziert (3000–50.000
Zufallseingaben, zusätzlich gegen `hashlib`).

### 7.1 Die Rundenfunktion, formal

Zustand (a,…,h) ∈ ({0,1}³²)⁸, Rundenkonstante Kₜ, Nachrichtenwort Wₜ:

```
Σ₀(x) = ROTR²(x) ⊕ ROTR¹³(x) ⊕ ROTR²²(x)
Σ₁(x) = ROTR⁶(x) ⊕ ROTR¹¹(x) ⊕ ROTR²⁵(x)
Ch(e,f,g)  = (e ∧ f) ⊕ (¬e ∧ g)
Maj(a,b,c) = (a ∧ b) ⊕ (a ∧ c) ⊕ (b ∧ c)

T₁ = h + Σ₁(e) + Ch(e,f,g) + Kₜ + Wₜ   (mod 2³²)
T₂ = Σ₀(a) + Maj(a,b,c)                (mod 2³²)

h′=g  g′=f  f′=e  e′=d+T₁
d′=c  c′=b  b′=a  a′=T₁+T₂
```

Sechs der acht Zuweisungen sind reine Umbenennungen — in Hardware Verdrahtung,
keine Gatter. Die Rotationen ebenfalls. Die Kosten sitzen in den fünf
modularen Additionen und in Ch/Maj.

### 7.2 Satz A — Minimalität der Bitfunktionen

Über der Klasse bitweiser Operationen {∧, ∨, ⊕, ¬} benötigt **Ch genau 3** und
**Maj genau 4** Operationen:

```
Ch(e,f,g)  = g ⊕ (e ∧ (f ⊕ g))            3 statt 4
Maj(a,b,c) = (a ∧ b) ⊕ (c ∧ (a ⊕ b))      4 statt 5
Maj(a,b,c) = (a ∧ b) ∨ (c ∧ (a ∨ b))      Alternative, gleiche Länge
```

*Beweis:* erschöpfende Breitensuche über alle kürzeren Schaltungen.

*Zur Vollständigkeit der Operationsklasse:* ADD, SUB und MUL erweitern die
Klasse nicht sinnvoll, da sie Überträge zwischen Bitpositionen erzeugen,
während Ch und Maj positionsweise unabhängig arbeiten. Der Minimalitätsbeweis
gilt damit für die vollständige Klasse zulässiger Operationen.

**Bilanz:** 24 statt 26 Operationen pro Runde (−7,7 %), über 64 Runden
128 Operationen.

### 7.3 Satz B — Zwei-Ketten-Darstellung

Die Register b, c, d sind zeitverschobene Kopien von a, ebenso f, g, h von e:

```
b_t = a_{t−1}   c_t = a_{t−2}   d_t = a_{t−3}
f_t = e_{t−1}   g_t = e_{t−2}   h_t = e_{t−3}
```

Damit ist die Kompressionsfunktion äquivalent zu **zwei gekoppelten
Rekursionen**:

```
T₁ = e_{t−4} + Σ₁(e_{t−1}) + Ch(e_{t−1}, e_{t−2}, e_{t−3}) + Kₜ + Wₜ
T₂ = Σ₀(a_{t−1}) + Maj(a_{t−1}, a_{t−2}, a_{t−3})
e_t = a_{t−4} + T₁
a_t = T₁ + T₂
```

In Hardware: zwei vierstufige Schieberegister statt acht Einzelregister.

| | Standard | Zwei-Ketten |
|---|---|---|
| Register-Kopien pro Runde | 6 | 0 |
| Registerschreibvorgänge | 8 | 2 |
| modulare Additionen | 7 | 7 |
| **Summe** | **25** | **13** |

Die Arithmetik bleibt identisch; es entfallen ausschließlich Datenbewegungen.

Eine weitere Variante fasst zwei Runden zusammen, sodass der Zwischenzustand
nie materialisiert wird — ebenfalls verifiziert.

### 7.4 Satz C — Sigma als carry-less Multiplikation

Σ₀ und Σ₁ sind XOR-Verknüpfungen von Rotationen, also **linear über GF(2)**.
Jede solche Abbildung ist eine zyklische Faltung, mithin eine carry-less
Multiplikation modulo (x³² − 1):

```
Σ₀(x) = x ⊛ 0x40080400
Σ₁(x) = x ⊛ 0x04200080
σ₀(x) = (x ⊛ C) ⊕ (x ≫ 3)          Schedule-Variante
```

Statt 3 Rotationen + 2 XOR: eine Polynommultiplikation. Auf x86 mit
PCLMULQDQ bzw. ARM mit PMULL ein einziger Befehl. Beim Schedule-σ₀ sinkt
die Operationszahl von 5 auf 3.

### 7.5 Carry-Save-Zerlegung der Additionen

Ein 3:2-Kompressor fasst drei Summanden zu zweien zusammen, ohne
Übertragskette:

```
s  = a ⊕ b ⊕ c
cy = ((a∧b) ∨ (a∧c) ∨ (b∧c)) ≪ 1
```

Verifiziert: (s + cy) ≡ (a+b+c) mod 2³². Die vier Additionen von T₁ werden
so zu drei CSA-Stufen plus einer echten Addition. In Software mehr
Operationen, in Hardware deutlich kürzerer kritischer Pfad.

---

## 8. Ringstruktur der linearen Schichten

Die Darstellung als Polynome erlaubt Aussagen, die auf Bitebene nicht
sichtbar sind.

**Modulus.** Über GF(2) gilt x³² + 1 = (x + 1)³² — verifiziert. Der Ring
GF(2)[x]/(x³²−1) ist damit **nicht halbeinfach**; er enthält Nilpotente.
Ein Element ist genau dann invertierbar, wenn es nicht durch (x+1) teilbar
ist, also wenn es eine **ungerade** Zahl von Termen hat.

**Invertierbarkeit.** Beide Sigma-Polynome haben genau 3 Terme:

| Funktion | Polynom | ggT mit x³²+1 | Inverses |
|---|---|---|---|
| Σ₀ | x³⁰ + x¹⁹ + x¹⁰ = 0x40080400 | 1 | 0xcbd1a68d |
| Σ₁ | x²⁶ + x²¹ + x⁷ | 1 | 0x6ab84f6c |

Probe C · C⁻¹ ≡ 1 bestätigt.

**Rang und Kern.** Unabhängige Bestätigung über Gauß-Elimination:

| Funktion | Rang | Kerndimension |
|---|---|---|
| Σ₀, Σ₁ | 32/32 | 0 |
| σ₀, σ₁ (Schedule) | 32/32 | 0 |

Alle vier sind **bijektiv** — kein Informationsverlust.

### 8.1 Konsequenz für Angriffstechniken

Dies ist die praktisch wichtigste Folgerung des Abschnitts.

**Differentielle Kryptanalyse.** Für eine bijektive GF(2)-lineare Abbildung
gilt Σ(a ⊕ b) = Σ(a) ⊕ Σ(b) **exakt**. Differenzen passieren die
Sigma-Schichten also mit Wahrscheinlichkeit 1, ohne jeden Verlust.

**Daraus folgt:** Der gesamte Wahrscheinlichkeitsverlust eines differentiellen
Pfades entsteht ausschließlich an

1. den modularen Additionen (Übertragsketten) und
2. Ch/Maj.

Die linearen Schichten tragen nichts bei — weder als Hindernis noch als
Hebel. Das erklärt, warum die publizierte SHA-2-Kryptanalyse sich auf die
Übertragsketten konzentriert.

**Lineare Kryptanalyse.** Masken lassen sich durch Multiplikation mit dem
Inversen rückwärts propagieren — geschlossene Formel statt Suche. Die
Inversen stehen in der Tabelle oben.

**Bereits gemessene Anschlusswerte:**

| Größe | Wert |
|---|---|
| ARX-Rotationswahrscheinlichkeit rotl(a+b) = rotl(a)+rotl(b) | 0,3749 (theoretisch 3/8) |
| DP der modularen Addition für Δ = 0x80000000 | **1,0000 exakt** |

Der zweite Wert ist der klassische Ausgangspunkt differentieller SHA-2-Pfade:
Eine Differenz im höchstwertigen Bit überlebt die Addition immer, weil dort
kein Übertrag entstehen kann.

**Einordnung.** Diese Umformungen ändern die Schwierigkeit von Angriffen
nicht. Sie lokalisieren sie präzise: in den Bausteinen mit Übertrag, nicht
in den linearen Schichten.

---

## 9. Gatterebenen-Repräsentation und daraus folgende Beweise

### 9.1 Die Repräsentationsfrage

K1 wurde vollständig auf Bitebene als And-Inverter-Graph (AIG) und als XAIG
(AIG mit nativen XOR-Knoten) konstruiert, mit strukturellem Hashing.

| Variante | AND | XOR | gesamt | Reduktion |
|---|---|---|---|---|
| AIG-Basis, RCA-Addition | 198.167 | — | 198.167 | — |
| XAIG (native XOR), OR-Übertrag | 49.265 | 49.634 | 98.899 | 50,1 % |
| XAIG + Carry-Save-Bäume | 61.338 | 50.172 | 111.510 | 43,7 % |
| XAIG + CSA, K1-1 | 50.954 | 42.094 | 93.048 | 53,0 % |
| **XAIG, AND-minimaler Übertrag** | **21.398** | 85.208 | 106.606 | — |

Die letzte Zeile ist nicht über die Gesamtzahl vergleichbar, sondern über die
**AND-Zahl** — siehe 9.8.

**Befund:** Rund die Hälfte aller Knoten sind XOR. Im reinen AIG kostet jedes
XOR drei AND-Knoten, im XAIG einen. Die Halbierung folgt also aus der
Repräsentationswahl, nicht aus Heuristik.

**Gegenbefund zu Carry-Save:** CSA-Bäume vergrößern den Graphen (111.510 statt
98.899). CSA spart Latenz auf dem kritischen Pfad, nicht Gatter. Zwei
verschiedene Kostenmetriken — eine Optimierung für die eine kann die andere
verschlechtern.

**Cut-Analyse (16 Runden):** 202.013 enumerierte 4-Cuts, 20.001 ausgewertete
Cut-Funktionen zerfallen in nur 509 verschiedene Klassen — Wiederverwendungsgrad
39-fach.

### 9.2 Korrektur zu Satz A

Die in 7.2 bewiesene Minimalität von Ch (3 Ops) und Maj (4 Ops) gilt für die
**Wortoperations-Metrik**. Auf Gatterebene ist die „optimierte" Form
durchgehend 1–2 % **größer**, weil XOR im AIG drei AND-Knoten kostet, ein
einfaches ∧ dagegen einen.

**Lehre:** Minimalität ist nur relativ zu einer Kostenmetrik definiert. Eine
Optimierung ohne Angabe der Metrik ist keine Aussage.

### 9.3 Multiplikative Komplexität

XOR-Knoten sind GF(2)-linear; AND-Knoten sind die **einzige**
Nichtlinearitätsquelle. Die AND-Zahl ist damit eine kryptanalytisch
bedeutsame Größe (multiplikative Komplexität).

| Runden | AND kumuliert | AND neu |
|---|---|---|
| 1–2 | **0** | 0 |
| 4 | 172 | 172 |
| 8 | 1.649 | 1.477 |
| 16 | 6.553 | 4.904 |
| 32 | 19.031 | 12.478 |
| 64 | **49.265** | 30.234 |

Etwa 3.000 AND-Gatter pro Runde im Mittel. Die Null in den Runden 1–2
bestätigt unabhängig die ANF-Messung aus Abschnitt 2 (Runde 2 vollständig
affin) — zwei methodisch getrennte Verfahren, gleiches Ergebnis.

### 9.4 Satz D — exakte Zahl affiner Ausgabebits

Ein Ausgabebit ist genau dann affin über GF(2), wenn sein Kegel im XAIG
**kein einziges AND-Gatter** enthält. Das ist per Graphtraversierung
entscheidbar — struktureller Beweis, keine Stichprobe.

| Runden | affine Bits von 256 |
|---|---|
| 1 | **256 (100 %)** |
| 2 | **256 (100 %)** |
| 3–8 | **0** |

Der Übergang ist scharf. K1 ist bis Runde 2 vollständig linear invertierbar,
ab Runde 3 kein einziges Bit mehr.

### 9.5 Satz E — Kollisionsfreiheit von K1-1

K1-1 besitzt exakt 65.536 mögliche Eingaben und ist damit erschöpfend prüfbar.

**Auf vollen 256 Bit ist K1-1 injektiv: null Kollisionen bei vollständiger
Prüfung aller Eingaben.** Das ist ein Beweis für diesen Eingaberaum, kein
Wahrscheinlichkeitsargument.

**Bei Trunkierung sind zwei Modelle zu unterscheiden**, die erst ab 24 Bit
zusammenfallen:

- **Paarzahl** n(n−1)/2 / 2ᵏ — erwartete Zahl kollidierender *Paare*. Gilt nur
  für großes k.
- **Belegungsdefizit** n − 2ᵏ(1 − e^(−n/2ᵏ)) — erwartete Zahl überzähliger
  Werte im Besetzungsmodell. Auch für kleines k gültig.

| Bits | gemessen | Paarzahl | Belegungsdefizit | Stdabw | Abweichung |
|---|---|---|---|---|---|
| 12 | 61.440 | 524.280,0 | 61.440,0 | 0,0 | −0,02 σ |
| 16 | 24.092 | 32.767,5 | 24.109,3 | 79,8 | −0,22 σ |
| 20 | 1.978 | 2.048,0 | 2.006,0 | 43,0 | −0,65 σ |
| 24 | 126 | 128,0 | 127,8 | 11,3 | −0,16 σ |
| 28 | 8 | 8,0 | 8,0 | 2,8 | ±0,00 σ |
| 32 | 1 | 0,5 | 0,5 | 0,7 | +0,71 σ |
| ≥ 40 | 0 | 0,0 | 0,0 | — | — |

**Einordnung.** Die 12-Bit-Zeile ist trivial: 65.536 Werte füllen 4.096 Fächer
mit Sicherheit vollständig, also gilt Kollisionen = n − 2ᵏ exakt, ohne dass ein
Modell etwas leistet. Der einzige echte statistische Test ist die 16-Bit-Zeile;
sie bestätigt mit −0,22 σ die Zufallshypothese. Die scheinbar hohe Präzision
(17 Werte Abweichung) ist bei einer Standardabweichung von 79,8 unauffällig.

### 9.6 Satz F — Injektivität bei reduzierten Runden

Ab Runde 8 ist K1-1 in jeder geprüften Rundenzahl injektiv (65.536
verschiedene Ausgaben). Für Runden 1–4 ist die Ausgabe konstant — nicht wegen
Informationsverlusts, sondern weil die freien Bits in W₇ liegen und erst ab
Runde 8 gelesen werden (vgl. Satz 6).

### 9.7 AND-minimale Übertragsform

Die bis hier verwendete Übertragsform des Volladdierers war die OR-Variante
(a∧b) ∨ (a∧c) ∨ (b∧c) — drei AND-Äquivalente je Bit. Die AND-minimale Form
kostet **ein** AND:

```
cy  = ((a ⊕ c) ∧ (b ⊕ c)) ⊕ c          1 AND, 3 XOR
Maj = ((a ⊕ b) ∧ (b ⊕ c)) ⊕ b          1 AND, 3 XOR
```

Beide Identitäten erschöpfend über alle acht Belegungen verifiziert.

| Variante | AND | XOR | AND-Tiefe |
|---|---|---|---|
| OR-Form | 53.448 | 53.769 | 3.199 |
| **AND-minimal** | **21.398** | 85.208 | **1.604** |

**Reduktion 60,0 % der AND-Gatter; die AND-Tiefe halbiert sich** (3.199 → 1.604),
weil pro Volladdiererbit eine AND-Stufe statt zwei anfällt.

**Analytische Nachrechnung.** Addition mit 31 AND (letzter Übertrag ungenutzt),
7 Additionen je Runde → 217, plus Ch (32) und Maj (32) = 281 je Runde;
×64 = 17.984. Schedule 48 × 3 × 31 = 4.464. Finaladdition 8 × 31 = 248.
Erwartet **22.696**, gemessen **21.398** — Differenz −5,7 % durch
Konstantenfaltung (ADD(Kₜ, Wₜ) mit konstantem Kₜ; Runden 8–15 mit beidseitig
konstanten Operanden) und strukturelles Hashing.

**Verifikation.** Der XAIG wurde knotenweise simuliert und mit `hashlib`
verglichen — fünf Zufallseingaben, exakte Übereinstimmung. Damit ist die Zahl
eine Aussage über eine Schaltung, die nachweislich SHA-256 berechnet, nicht
nur über eine Wortformel. Zusätzlich wurde die AND-minimale Maj-Form in einer
vollständigen SHA-256-Referenzimplementierung gegen `hashlib` geprüft
(vier Testvektoren, inkl. Mehrblock).

**Verschärfung von Lehre 6.** Die beiden Maj-Formen kosten in der
Wortoperations-Metrik **identisch** (je 4 Operationen) und in der AND-Metrik
**Faktor 3**. Das ist ein schärferes Beispiel als die Ch-Form aus 9.2, wo der
Unterschied nur 1–2 % betrug.

**Einordnung des CSA-Gegenbefunds (9.1).** Der 3:2-Kompressor aus 7.5 ist genau
diese Maj-Funktion. Der dort gemessene Nachteil der Carry-Save-Bäume erklärt
sich damit in derselben Rechnung: Sie wurden mit der OR-Form gebaut.

### 9.8 Kalibrierung gegen die Literatur

Die Bristol-Fashion-Referenzschaltung für SHA-256 wird in der MPC-Literatur mit
**22.573 AND-Gattern** angegeben. Sie bildet einen freien 512-Bit-Block und
einen freien 256-Bit-Chaining-State auf den neuen State ab — also mit mehr
freien Eingängen als K1, wo Padding und IV konstant sind.

Nachbau der vergleichbaren Variante:

| Variante | AND | XOR | AND-Tiefe |
|---|---|---|---|
| **eigene Nachbildung (Block + State frei)** | **22.573** | 91.650 | 1.607 |
| publizierte Bristol-Fashion-Referenz | **22.573** | — | — |
| K1 (Padding + IV konstant) | 21.398 | 85.208 | 1.604 |

**Abweichung: exakt null Gatter.** Bei über 22.000 nichtlinearen Gattern und
unabhängiger Konstruktion. Der Graph wurde zusätzlich knotenweise gegen eine
Referenzkompression simuliert.

Damit ist die Werkzeugkette gegen einen externen Standard validiert — die
Positivkontrolle aus Lehre 2, angewandt auf das Messinstrument selbst. Die
Differenz von 1.175 AND (5,2 %) zwischen beiden Varianten ist die Ersparnis
durch festes Padding und konstanten IV.

### 9.9 AND-Tiefe pro Rundenzahl

Die AND-Tiefe ist die maßgebliche Kostengröße für FHE (Zahl der nötigen
Bootstrapping-Schritte).

| Runden | AND | XOR | AND-Tiefe | Tiefe/Runde |
|---|---|---|---|---|
| 1 | 172 | 349 | 30 | 30,0 |
| 2 | 442 | 1.206 | 54 | 27,0 |
| 8 | 2.232 | 7.456 | 204 | 25,5 |
| 16 | 4.215 | 14.894 | 404 | 25,2 |
| 32 | 9.495 | 36.026 | 804 | 25,1 |
| 64 | 21.398 | 85.208 | **1.604** | 25,1 |

Die Tiefe wächst nach den ersten Runden **exakt linear mit 25,1 Stufen je
Runde** und ist damit vorhersagbar statt messbedürftig.

**Export.** Der Graph liegt im Bristol-Fashion-Format vor
(`K1_bristol.txt`, 126.746 Gatter, 127.002 Drähte, 3,2 MB) — passend zur
Literaturangabe von 3,5 MB für die Kompressionsfunktion in diesem Format.

### 9.10 Cut-Rewriting: der Graph ist beweisbar optimal

**Maßstab.** Für jeden 4-Cut wird die multiplikative Komplexität (MC) seiner
Funktion mit dem tatsächlichen AND-Verbrauch im Kegel verglichen. Die MC
**aller 65.536 Vierbit-Funktionen** wurde erschöpfend bestimmt:

| MC | Funktionen |
|---|---|
| 0 | 32 |
| 1 | 1.120 |
| 2 | 30.720 |
| 3 | 32.768 |

**Ergebnis.** 637.964 enumerierte 4-Cuts, alle 21.398 AND-Knoten geprüft:

| Differenz ist − soll | Anzahl |
|---|---|
| 1 | **5** |
| 0 | **21.393** |

**21.393 von 21.398 Knoten liegen exakt auf der Untergrenze.** Die obere
Schranke der Einsparung beträgt 5 Gatter = **0,02 %**, real weniger, da sich
Cuts überlappen.

Der Graph ist damit bezüglich 4-Cut-Rewriting **beweisbar optimal** — nicht
heuristisch ausgereizt, sondern auf der bewiesenen Untergrenze.

**Korrektur einer früheren Schätzung.** In 9.1 wurden „40–50 % durch
Rewriting" erwartet. Tatsächlich stammen die Gewinne vollständig aus
Konstruktionsentscheidungen — 50 % aus der Repräsentationswahl (XAIG statt
AIG), 60 % aus der Übertragsform — und 0,02 % aus dem Rewriting selbst.

**Lehre daraus:** Bei einer XOR-lastigen Funktion entscheidet die Wahl von
Repräsentation und Grundbausteinen über die Größenordnung; Rewriting-Heuristiken
holen anschließend nichts mehr. Die Reihenfolge ist nicht umkehrbar.

### 9.11 Wofür die Reduktion real nutzbar ist

**Verwertbar:** In MPC, FHE und Zero-Knowledge-Beweisen über SHA-256 ist die
AND-Zahl die maßgebliche Kostengröße — XOR ist dort praktisch gratis. Die
Halbierung von 198.167 auf 98.899 halbiert dort die Kosten tatsächlich.

**Begrenzt verwertbar:** Kleinere CNF-Formeln für SAT-Kodierung (linear in der
Gatterzahl). Erwarteter Effekt auf die erreichbare Rundenzahl bei
Preimage-Angriffen: null bis eine Runde, da der Suchraum exponentiell bleibt.

**Nicht verwertbar:** Für Preimage- oder Kollisionsangriffe auf volles
SHA-256. Multiplikative Komplexität misst Berechnungskosten, nicht
Invertierungskosten.

---

## 10. K0 — der erste Hash-Durchlauf

K1 ist der **zweite** Durchlauf. Der erste läuft über den 80-Byte-Header und
zerfällt in zwei Blöcke:

| Block | Inhalt | Rolle |
|---|---|---|
| 1 | Byte 0–63 | ergibt den Midstate, nonce-unabhängig |
| 2 | Byte 64–79 + Padding | **K0** |

**Eingabewörter von K0:**

| Wort | Inhalt | Status |
|---|---|---|
| W₀ | Byte 64–67: MerkleRoot-Ende | konstant |
| W₁ | Byte 68–71: Time | konstant je Template |
| W₂ | Byte 72–75: Bits | konstant |
| **W₃** | **Byte 76–79: Nonce** | **frei, 2³²** |
| W₄ | Padding 0x80000000 | konstant |
| W₅–W₁₄ | Null | konstant |
| W₁₅ | 640 (= 80 Byte in Bit) | konstant |

### 10.1 Strukturvergleich

| | K0 | K1-1 |
|---|---|---|
| Lage der freien Bits | W₃ | W₇ |
| freie Bits | 32 | 16 |
| konstanter Vorlauf | **3 Runden** | **7 Runden** |
| Eingaben | 2³² | 2¹⁶ |
| erschöpfbar in | ~1,7 Stunden | Sekunden |

**Lawineneffekt bei gekipptem Nonce-Bit:**

| Runde | diff. Bits von 256 | Anteil |
|---|---|---|
| 3 | 0,0 | 0,0 % |
| 4 | 3,8 | 1,5 % |
| 6 | 55,6 | 21,7 % |
| 8 | 114,9 | 44,9 % |
| 12 | 127,5 | 49,8 % |
| ≥16 | ~128 | ~50 % |

Sättigung nach 10–12 Runden — dieselbe Kurve wie bei K1. Die Lage der freien
Bits verschiebt den Startpunkt, ändert aber die Diffusionsgeschwindigkeit nicht.

### 10.2 Durchlauf

400.000 Nonces in 0,6 s (695.281 H/s in reinem Python). Bestes Ergebnis:
Nonce 86.604 mit 16 führenden Nullbits. Die Verteilung folgt exakt 2⁻ᵏ über
alle 17 belegten Stufen.

### 10.3 Methodische Einordnung

K0 ist das Objekt, auf das es praktisch ankommt — der Suchraum eines Miners
besteht bei festem Template genau aus diesen 2³² Nonces.

Für die Analyse ist es jedoch **schlechter geeignet** als K1-1: weniger
konstanter Vorlauf, mehr Eingaben, gleiche Sättigung.

**Das ist eine Aussage über die Methodik:** Die Variante, die Bitcoin am
nächsten liegt, gibt strukturell am wenigsten her; die am besten analysierbare
(K1-1) liegt am weitesten davon entfernt. Befunde an K1-1 sind daher nicht
automatisch auf K0 übertragbar — Abschnitt 6 zeigt dies bereits für die
Restsymmetrie, die dort ausschließlich aus der Lage der freien Bits in W₇ folgt.

---

## 11. Linearisierte Nachrichtenexpansion als GF(2)-Code

Die echte Expansion nutzt modulare Addition und ist nicht GF(2)-linear. Die
**Linearisierung** ersetzt + durch ⊕:

```
W_t = σ₁(W_{t−2}) ⊕ W_{t−7} ⊕ σ₀(W_{t−15}) ⊕ W_{t−16}
```

Das ist die Standardnäherung für lineare Charakteristiken. Das Minimalgewicht
des entstehenden Codes ist eine untere Schranke für die Zahl aktiver Bits jeder
rein linearen kollisionssuchenden Charakteristik.

### 11.1 Codeparameter

| Variante | Dimension | Länge |
|---|---|---|
| freier Block (publizierter Fall) | 512 | 2048 |
| **festes Padding (K1)** | **256** | 2048 |

Unter festem Padding halbiert sich die Dimension; das Ergebnis ist daher nicht
aus dem publizierten Fall ableitbar.

### 11.2 Minimalgewicht

**Verfahren:** Informationsmengen-Dekodierung mit echter Spaltenpermutation,
Lee-Brickell-Kombinationen bis Tripel, lokale Nachbarschaftssuche.

| Code | Iterationen | Verbesserungen | Minimalgewicht |
|---|---|---|---|
| [2048, 512] | 1.659 | **0** | **467** |
| [2048, 256] | 2.090 | **0** | **467** |

Nach 3.749 Iterationen ohne eine einzige Verbesserung ist 467 sehr
wahrscheinlich das **echte** Minimalgewicht, nicht nur eine schwache obere
Schranke.

**Beide Codes liefern dasselbe Ergebnis** — gleiches Gewicht, gleiches Profil,
44 aktive Wörter. Das Codewort niedrigsten Gewichts liegt bereits im kleineren
Unterraum; die Halbierung der Dimension entfernt es nicht.

**Profil:** `[1, 0, …, 0, 1, 0, 3, 0, …]` — ein einzelnes aktives Bit in W₀,
das über die Expansion 466 Bits in W₁₆–W₆₃ aktiviert und 44 der 64 Wörter
berührt.

| Bereich | Gewicht |
|---|---|
| W₀–W₁₅ | 1 |
| W₁₆–W₆₃ | 466 |

### 11.3 Bedeutung

Jede rein lineare kollisionssuchende Charakteristik über 64 Runden hat
mindestens 467 aktive Bits. Bei einer differentiellen Wahrscheinlichkeit von
höchstens ½ je aktivem Bit ergibt sich eine Kostenschranke von **2⁻⁴⁶⁷** —
weit jenseits von 2⁻²⁵⁶, also jenseits von Brute Force.

Das erklärt quantitativ, warum die publizierten Angriffe **nicht** rein linear
arbeiten, sondern lokale Kollisionen mit nichtlinearen Anfangsrunden verwenden.

**Einschränkung:** Die Linearisierung ist eine Näherung. Überträge der echten
modularen Addition können Differenzen dämpfen oder verstärken; die Schranke
gilt streng nur für rein lineare Charakteristiken.

---

## 12. RX-Kryptanalyse

Die Messungen in Abschnitt 5 prüften reine Rotationserhaltung. Die
**RX-Kryptanalyse** (Rotational-XOR, Ashur/Liu) verfolgt stattdessen gekoppelte
Differenzen aus Rotation und XOR.

**Ansatzpunkt bei K1:** Da W₈–W₁₅ konstantes Padding sind, existiert in den
Runden 8–15 ein achtrundiges Fenster, in dem **keine neuen
Nachrichtendifferenzen** in den Zustand injiziert werden. Die Frage: Überlebt
eine in Runde 7 aufgebaute RX-Differenz dieses Fenster?

### 12.1 Grundlage

RX-Propagation durch die modulare Addition, gemessen an 200.000 Paaren:

| r | P(RX überlebt) | theoretisch ¼(1 + 2⁻ʳ + 2^−(32−r) + 2⁻³²) |
|---|---|---|
| 1 | 0,3761 | 0,3750 |
| 2 | 0,3104 | 0,3125 |
| 4 | 0,2648 | 0,2656 |
| 8 | 0,2502 | 0,2510 |
| 16 | 0,2496 | 0,2500 |

Übereinstimmung mit der Theorie — die bekannte ARX-RX-Eigenschaft ist
reproduziert.

**Korrektur (Nachprüfung 19.1).** Frühere Fassungen nannten hier 0,6250 /
0,4375 / 0,2812 / 0,2510. Nur der letzte Wert war richtig. Die Zahlen stammten
aus einer fehlerhaften Kommentarzeile in `rx_analyse.py` („für r=1 liegt die
Wahrscheinlichkeit bei ~0.625"); das Skript selbst gibt die obigen Werte aus.
Sie widersprachen zudem Abschnitt 8.1, wo dieselbe Größe mit 0,3749 korrekt
angegeben ist. Unabhängig nachgemessen: 0,3756 / 0,3107 / 0,2677 / 0,2521.
Die Schlussfolgerung von Abschnitt 12 ist unberührt — sie hängt an 12.2 und
12.3, nicht an dieser Tabelle.

### 12.2 Der entscheidende Test

Der Zustand nach Runde 7 wurde als **perfektes RX-Paar gesetzt** (nicht
mühsam aufgebaut, sondern geschenkt) und dann durch das Fenster laufen
gelassen:

| r | nach Runde 8 | nach 12 | nach 16 | nach 24 |
|---|---|---|---|---|
| 1 | 100,00 % | 49,88 % | 49,74 % | 50,08 % |
| 2 | 100,00 % | **54,07 %** | 50,10 % | 49,98 % |
| 4 | 100,00 % | 51,67 % | 49,89 % | 49,78 % |
| 8 | 100,00 % | 50,51 % | 50,36 % | 50,21 % |

**Die Relation stirbt innerhalb von vier Runden.** Bei r = 2 bleibt in Runde 12
ein Rest von 4 Prozentpunkten; ab Runde 16 ist auch der verschwunden.

### 12.3 Der strukturelle Grund

Für eine RX-Differenz müsste gelten:

```
K_t = rotl(K_t, r)
```

Diese Gleichung erfüllen über 32 Bit **nur** 0x00000000 und 0xFFFFFFFF.
**Keine der 64 Rundenkonstanten erfüllt sie.** Beispiel für das Fenster:

| Runde | Kₜ | rotl(Kₜ,1) |
|---|---|---|
| 8 | 0xd807aa98 | 0xb00f5531 |
| 12 | 0x72be5d74 | 0xe57cbae8 |
| 15 | 0xc19bf174 | 0x8337e2e9 |

**Das konstante Nachrichtenfenster existiert, ist aber wirkungslos:** Die
Rundenkonstanten laufen weiter und brechen die RX-Relation in jeder einzelnen
Runde neu — unabhängig davon, ob Nachrichtendifferenzen injiziert werden.

Das ist konsistent mit der Kausalanalyse aus 5.1: Konstanten brechen Symmetrien,
und sie tun es nachweislich auch dort, wo die Nachricht keine Differenz liefert.

### 12.4 Bewertung weiterer vorgeschlagener Vektoren

| Ansatz | Bewertung |
|---|---|
| **Neuronale Distinguisher** (Gohr 2019) | Real und etabliert, aber sie *detektieren* Bias, sie erzeugen keinen. Der Lawineneffekt sättigt bei exakt 50,000 % ab Runde 10 (Abschnitt 2). Ein Netz kann dort nichts finden, was nicht vorhanden ist. Gohrs Erfolg betraf 8-Runden-Speck32/64 — eine deutlich schwächere Konstruktion. |
| **Invariante Unterräume** (Leander et al.) | Technisch möglich, für ARX praktisch aussichtslos: Die modulare Addition respektiert keine Unterraumstruktur, weil Überträge zwischen Bitpositionen wandern. |
| **SAT-Injection aus Cut-Klassen** | Beruht auf einem Missverständnis: Cut-Klassen beschreiben lokale Topologie, die CDCL über Unit Propagation ohnehin nutzt. Learned Clauses entstehen aus Konflikten, nicht aus Struktur. |

---

## 13. Struktur zwischen gültigen Eingaben

### 13.1 Was ein Rangtest leistet — und was nicht

Ein GF(2)-Rangtest über einer Menge gültiger Eingaben schließt **ausschließlich
lineare** Abhängigkeiten aus. Kryptographische Funktionen sind gerade darauf
ausgelegt, diesen Test zu bestehen; Relationen aus modularer Addition, Ch/Maj
oder anderen nichtlinearen Operationen erscheinen darin als Rauschen.

Die Verallgemeinerung ist der Rang über Monomen vom Grad ≤ d. Dabei zeigt sich
die eigentliche Grenze — sie liegt **nicht bei der Analysemethode, sondern bei
der Stichprobengröße**:

| Grad d | Monome C(256, ≤d) | nötige gültige Eingaben |
|---|---|---|
| 1 | 257 | 257 |
| 2 | 32.897 | 32.897 |
| 3 | 2.796.417 | 2.796.417 |
| 4 | 177.589.057 | 177.589.057 |

Jede gültige Eingabe kostet 2ᵏ Hashes bei Schwelle k. Daraus die Gesamtkosten
(als log₂ der Hash-Auswertungen):

| Schwelle | Grad 1 | Grad 2 | Grad 3 |
|---|---|---|---|
| 20 Bit | 2²⁸ | 2³⁵ | 2⁴¹ |
| 32 Bit | 2⁴⁰ | 2⁴⁷ | 2⁵³ |
| **79 Bit (Mining)** | **2⁸⁷** | **2⁹⁴** | **2¹⁰⁰** |

Das Bitcoin-Netzwerk hat in 17 Jahren rund 2⁹⁶ Hashes berechnet (Abschnitt 4.7).
Ein Grad-2-Test auf Mining-Niveau bräuchte 2⁹⁴ allein für die Beschaffung der
Stichprobe.

**Formulierung des Ergebnisses:** Verfahren wie Gröbnerbasen, SAT-Solver oder
neuronale Netze könnten Beziehungen höheren Grades prinzipiell finden. Sie
scheitern hier nicht an ihrer Ausdrucksstärke, sondern daran, dass die
Datenpunkte, auf denen sie arbeiten müssten, so teuer sind wie das Mining
selbst.

**Kein Test beweist die Abwesenheit von Struktur.** Jeder bestätigt nur das
Fehlen genau des Musters, nach dem er sucht.

### 13.2 Schranken für den Abstand gültiger Eingaben

Sei S = {x : K1(x) < T}. Unter Gleichverteilungsannahme gilt |S| ≈ 2²⁵⁶⁻ᵏ bei
Schwelle k — beim Mining-Target (k ≈ 79) also **|S| ≈ 2¹⁷⁷**.

**Obere Schranke des Minimalabstands (Kugelpackungsschranke).** Hätte S
Minimalabstand d, müssten |S| disjunkte Hamming-Kugeln vom Radius d/2 in den
Raum passen:

```
|S| · V(d/2) ≤ 2²⁵⁶
```

Mit |S| = 2¹⁷⁷ folgt V(d/2) ≤ 2⁷⁹. Über die Entropieabschätzung
V(r) ≈ 2^(256·H(r/256)) ergibt sich r ≈ 14, also:

> **d ≤ 28** — es existieren zwangsläufig zwei gültige Eingaben mit
> Hamming-Abstand höchstens 28.

Diese Aussage folgt allein aus der Mächtigkeit von S, ohne weitere Annahme über
die Struktur von SHA-256.

**Untere Schranke: existiert nicht.** Es gibt 256 · 2²⁵⁵ Paare mit Abstand 1;
jedes ist mit Wahrscheinlichkeit 2⁻¹⁵⁸ beidseitig gültig. Der Erwartungswert
für Paare im Abstand 1 ist damit astronomisch groß. Ein nichttrivialer
Mindestabstand kann nicht existieren. Für die arithmetische Differenz
e₁ − e₂ gilt dasselbe.

**Einschränkung.** Die Kugelpackungsschranke selbst ist unbedingt, benötigt aber
|S|. Dieser Wert folgt aus der Gleichverteilungsannahme — dieselbe Lücke wie an
allen anderen Stellen dieses Dokuments.

**Offener, messbarer Punkt:** Bei niedriger Schwelle (z. B. 20 Bit) lässt sich
der tatsächliche Minimalabstand einer Stichprobe bestimmen und gegen die
Kugelpackungsvorhersage halten. Das prüft die Gleichverteilungsannahme
empirisch.

### 13.3 Methodenwarnung aus einem eigenen Fehlversuch

Ein Durchlauf zur Erzeugung gültiger Eingaben lieferte scheinbar dramatische
Struktur: Rang 28 statt 200, mittlerer Hamming-Abstand 13,93 statt erwarteter
128,0.

**Das war ein Artefakt der Stichprobenerzeugung.** Die Eingaben wurden als
aufsteigende Zähler `1, 2, 3, …` in 32-Byte-Darstellung gebildet; alle Treffer
lagen unter 2¹⁷, sodass die oberen 239 Bit durchgehend null waren. Der
niedrige Rang war eine Eigenschaft des Zählers, nicht von SHA-256.

Unberührt davon blieb der einzige nichtlineare Test (Wirkung von Differenzen
gültiger Paare auf zufälligen Basiswerten): −0,09 σ gegen −0,94 σ der
Kontrollgruppe — kein Effekt.

**Lehre:** Die Erzeugungsvorschrift der Stichprobe ist Teil des Experiments.
Ein Zähler ist keine Zufallsquelle.

---

## 14. Was nicht beweisbar ist

**Nichtexistenz einer kleineren Schaltung im Bereich 60–747 Gatter.** Dies
erfordert superlineare untere Schranken für explizite Funktionen — ein offenes
Problem der Komplexitätstheorie. Der Weltrekord liegt bei ~3,01n, für 16
Eingänge also unter 50 Gattern.

Exakte SAT-Synthese kann „keine Schaltung mit ≤ g Gattern" beweisen, praktisch
nur bis g ≈ 10 — unterhalb der Abzählschranke von 60 und damit ohne
Neuigkeitswert.

**Nichtexistenz eines Urbilds von H = 0.** Nur als Erwartungswert bestimmbar:
Ohne die Relation W₀ ≡ −σ₀(W₁) existiert erwartungsgemäß 1 Lösung; die Relation
entfernt 32 Bit Suchraum und senkt die Erwartung auf 2⁻³². Das System wird also
mit Wahrscheinlichkeit ~1−2⁻³² unerfüllbar — durch Abzählung, nicht durch
Kryptanalyse.

---

## 15. Methodische Lehren

1. **Kontrollgruppe ist nicht optional.** Bei jeder Suchmethode dieselbe Suche
   auf Zufallsdaten mitlaufen lassen. Ohne sie ist eine Trefferquote nicht
   interpretierbar. Dies hätte die historische >70-%-Beobachtung sofort erklärt.

2. **Positivkontrolle einbauen.** Lawineneffekt und Bit-Bias erkannten die
   degenerierte Variante (K = 0) nicht — die Tests waren blind für Symmetrien.
   Erst der Rotationstest bestand seine eigene Positivkontrolle.

3. **Cube-Summen liefern nur untere Schranken.** Bei 25 Cubes wurden 21 Bits mit
   Grad ≥4 gefunden, bei 800 Cubes 175. Der niedrige Wert war Messartefakt.

4. **Identische Abtastung für alle Kandidaten.** Ein scheinbarer Effekt
   (Kubikwurzeln z = +1,07 in K1-1) verschwand bei gleicher Abtastung.

5. **Sparsamkeitsdruck kleiner als das Nutzsignal halten.** Ein Druck von
   0,0008/Knoten bei einem Signalunterschied von 0,0006 lehrt die Evolution,
   kleine statt gute Formeln zu bevorzugen.

6. **Minimalität ist metrikabhängig — und der Unterschied kann Faktor 3
   betragen.** Die beiden Maj-Formen kosten in Wortoperationen identisch
   (je 4) und in AND-Gattern Faktor 3 (3 gegen 1). Ch mit 3 statt 4
   Wortoperationen ist auf Gatterebene 1–2 % *größer*. Carry-Save spart
   Latenz und kostet Gatter. Eine Optimierungsaussage ohne Angabe der
   Kostenmetrik ist keine Aussage.

7. **Mittelungsbereich vor der Messung festlegen.** Der Quadratwurzel-Befund
   entstand, weil über genau die vier Runden gemittelt wurde, in denen ein
   Artefakt wirkt. Über 8 oder 16 Runden verschwindet er.

8. **Entartungen zwischen Parametern prüfen.** Zwei Konstantensätze aus
   derselben Bildungsvorschrift können identische Werte enthalten. Die
   Differenz betrug hier 4,71 Sigma — mehr als jeder echte Effekt der Messreihe.

9. **Die Erzeugungsvorschrift der Stichprobe ist Teil des Experiments.**
   Ein aufsteigender Zähler als Eingabequelle erzeugte scheinbar dramatische
   Struktur (Rang 28 statt 200), die vollständig aus der Zählerform stammte
   (Abschnitt 13.3). Zufallsquelle statt Zähler.

10. **Repräsentation vor Heuristik.** Die 50-%-Reduktion des Graphen kam
   nicht aus Rewriting-Heuristiken, sondern aus der Wahl der richtigen
   Darstellung (XAIG statt AIG für eine XOR-lastige Funktion).

11. **Ephemere Mini-Batches statt fixem Holdout.** Auswendiggelerntes pflanzt
   sich nicht fort; Generalisierung wird in die Fitness eingebaut.

12. **Die naheliegende Ursache ist nicht die richtige.** Die Bitebenen-Kopplung
   wurde zunächst den Rechtsschiften zugeschrieben. Der faktorielle Test
   (18.6) zeigt: Schift und Rotation sind ununterscheidbar, entscheidend ist
   allein die Richtung. Eine Ursachenvermutung ohne Variantentest ist eine
   Vermutung.

13. **Jede Lösung braucht eine Probe im eigenen Modell.** Der Löser in 18.4
   lieferte ein plausibles Endergebnis aus einer falschen Rechnung. Aufgefallen
   ist es nur, weil die linearisierte Lösung im linearisierten Modell geprüft
   wurde — ein Test, der bei korrektem Löser trivial besteht und deshalb leicht
   weggelassen wird.

14. **Kommentare im eigenen Code sind keine Messwerte.** Tabelle 12.1 übernahm
   eine falsche Kommentarzeile statt der danebenstehenden Skriptausgabe
   (19.2). Zahlen gehören aus dem Programmlauf ins Dokument, nicht aus der
   Prosa daneben.

15. **Gierige Suche auf der falschen Granularität ist schlechter als eine
   feste Reihenfolge.** Bitweise Auswahl fand bei r = 17 eine Ratemenge von 73
   statt 64 Bits (20.4), weil der Propagationsgewinn erst beim vollständigen
   Wort anfällt und eine myopische Auswahl ihn nicht kommen sieht. Vor jeder
   Heuristik ist zu klären, in welchen Quanten das Nutzsignal überhaupt
   auftritt.

16. **Erfüllbar konstruierte Instanzen messen Struktur, nicht Machbarkeit.**
   In Abschnitt 20 ist die Lösung bekannt und wird beim Raten verwendet; es
   gibt keine Rückverfolgung. g(r) ist deshalb eine untere Schranke für den
   Suchaufwand und keine Laufzeit. Das ist gewollt — aber es muss dabeistehen.

---

## 16. Offene, erreichbare Fragen

- **Schaltungsminimierung im Bereich 60–747.** Cut-Rewriting auf dem bestehenden
  Graphen; realistisch 20–40 % zusätzliche Reduktion, semantikerhaltend.
- ~~Absicherung des Quadratwurzel-Befunds~~ — **erledigt**, als Artefakt
  aufgeklärt (Abschnitt 5.1). Damit ist kein Befund des Tages mehr offen,
  der eine Kontrollgruppe überlebt hätte.
- **Rundenreduziertes SHA-256.** Forschungsfront: Kollisionen bis Runde 31,
  Preimages bis 17–18, semi-free-start bis 38. Volle 64 Runden in keiner
  Disziplin angetastet.

- ~~Rückwärtsrechnung von K1~~ — **bearbeitet** (Abschnitt 18). Deterministisch
  über alle 64 Runden; die Sperre ist auf den Richtungskonflikt zwischen
  Übertrag und linearer Schicht lokalisiert und beziffert (Satz I).
- ~~Neutrale Bits bei r = 17~~ — **erledigt** (Abschnitt 21). Ergebnis: null
  von 64 geratenen Bits sind neutral, über zehn Instanzen reproduziert. Der
  Sprung von g(16) = 0 auf g(17) = 64 ist damit kein Messartefakt eines zu
  groß geratenen Backdoors, sondern die tatsächlich benötigte Zahl.
- **CDCL gegen Guess-and-Determine.** Abschnitt 20 misst
  Unit-Propagation. Ob Konfliktlernen die Kurve verschiebt, ist die offene
  Hälfte von 17.3 und braucht ein Solver-Binary.
- **Variante T mit schrittweise wiedereingesetzten Rechtsrotationen.** Die
  Reichweitentabelle in 18.8 sagt eine Klippe voraus. Direkt messbar wäre, ob
  ein Fensterlöser mit w+1 Ebenen die vorhergesagten Kosten trifft.

**Nicht erreichbar über diese Wege:** ein Angriff auf volles SHA-256 oder
Bitcoin-Mining. Preimage-Attacken auf reduzierte Runden lassen sich nicht
verketten, weil beide Teilangriffe ihren Treffpunkt frei wählen müssen, um
zu funktionieren — verkettet verliert der zweite genau diese Freiheit.

---

## 17. Ausblick: konkrete Folgeaufgaben

Nach Wert geordnet. Die Punkte 1–3 der ursprünglichen Aufgabenliste sind
abgearbeitet (Abschnitte 9.7 bis 9.10).

### 17.1 ~~Der erste Hash-Durchlauf~~ — erledigt (Abschnitt 10)

Erledigt: Abschnitt 10 definiert und vermisst K0. Satz 8 ist als bekannter
ASIC-Early-Exit eingeordnet.

**Offen bleibt** die vollständige Erschöpfung des 2³²-Raums (~1,7 Stunden
Rechenzeit) und die exakte ANF von K0, die bei 32 freien Bits nicht mehr per
Möbius-Transformation über den ganzen Raum berechenbar ist.

### 17.2 ~~Linearisierte Nachrichtenexpansion~~ — erledigt (Abschnitt 11)

Erledigt: Minimalgewicht 467 für beide Codes, 3.749 Iterationen ohne
Verbesserung. **Offen bleibt** ein exakter Beweis der Minimalität — dafür wären
Brouwer-Zimmermann-Schranken nötig, die erheblich mehr Rechenzeit erfordern.

### 17.3 ~~Werkzeugkette gegen die Forschungsfront kalibrieren~~ — Werkzeug gebaut, Messung siehe Abschnitt 20

Die Kodierung liegt vor und ist verifiziert (`k1_sat_kodierung.py`,
Abschnitt 20.1). Die eigentliche Kalibrierung gegen einen externen CDCL-Solver
steht noch aus und erfordert ein Solver-Binary; das Messgerüst dafür ist
`k1_sat_messlauf.py`.

**Ohne externen Solver bereits erledigt:** Abschnitt 20 misst die
Fortschrittskurve über eine eigene Propagationsmaschine und liefert damit die
gesuchte Zahl für die eigene Reichweite — allerdings für ein
Guess-and-Determine-Verfahren, nicht für CDCL.

Zur Einordnung der Literaturfront: praktische SAT-Preimages reichen bis
17–18 Runden (19 abgeschwächt), praktische Kollisionen bis 31 Runden.
Theoretische MITM- und Biclique-Preimages reichen bis etwa 45 Schritte, aber
mit Komplexität knapp unter 2²⁵⁶ und damit ohne nennenswerten Gewinn
gegenüber Brute Force.

### 17.4 Die Prognose aus 9.11 messen

Dort steht „null bis eine Runde" als erwarteter Effekt der kleineren CNF auf
die erreichbare Rundenzahl. Mit 17.3 im Rücken ist das direkt messbar und wird
zur Messung statt zur Schätzung.

### 17.5 Positionsvariante von K1-1

Die bisherigen K1-1[p] variieren den **Füllwert** bei gleichbleibender Lage der
freien Bits in W₇. Abschnitt 6 führt die Restsymmetrie gerade auf diese Lage
zurück.

Eine Variante mit den freien Bits in **W₀** trennt Eigenschaft von SHA-256 und
Eigenschaft der Einschränkung sauber und liefert eine zweite erschöpfend
prüfbare Instanz.


---

## 18. Rückwärtsrechnung: Reparametrisierung über W₄₈…W₆₃

Der Ausgangspunkt dieses Abschnitts ist die Frage, wie weit sich K1 vom
bekannten Endzustand her deterministisch zurückrechnen lässt. Satz 3 liefert
unter H = 0 den vollständigen Zustand nach Runde 64; die Rundenfunktion ist bei
bekanntem Wₜ exakt invertierbar. Die eigentliche Sperre liegt daher nicht in der
Rundenfunktion, sondern in der Nachrichtenexpansion.

Alle Aussagen dieses Abschnitts sind gegen `hashlib` verifiziert.

### 18.1 Schedule-Inversion und Bijektion

Die Expansion ist exakt umkehrbar:

```
W_{t−16} = W_t − σ₁(W_{t−2}) − W_{t−7} − σ₀(W_{t−15})   mod 2³²
```

Absteigend für t = 63 … 16 ausgewertet, stehen alle rechts vorkommenden Indizes
oberhalb von t−16. Die Rekursion ist damit wohldefiniert, und die Abbildung

> (W₄₈…W₆₃) ⟷ (W₀…W₁₅)

ist eine **Bijektion auf 512 Bit**.

| Prüfung | Fälle | Ergebnis |
|---|---|---|
| W₀…W₁₅ → Expansion → Schwanz → Rückrechnung | 2000 | bitidentisch |
| Zufallsschwanz → Kopf → Expansion → Schwanz | 2000 | bitidentisch |
| K1 über die Schwanz-Parametrisierung gegen `hashlib` | 300 | identisch |

**Nutzen der Reparametrisierung:** In dieser Form ist die Rückwärtsrichtung
durchgehend deterministisch, und die gesamte Schwierigkeit kondensiert in eine
einzige Bedingung statt in eine über die Runden verteilte Kette.

### 18.2 Satz G — deterministische Rückwärtstiefe

**Satz G.** Bei fester Wahl von W₄₈…W₆₃ ist der Rückwärtslauf über alle
**64 Runden** eine Funktion, keine Suche. Es existiert kein Verzweigungspunkt.

*Beweis: konstruktiv. Die Rundeninversion*

```
a = B,  b = C,  c = D,  e = F,  f = G,  g = H
T₂ = Σ₀(a) + Maj(a,b,c)
T₁ = A − T₂
d  = E − T₁
h  = T₁ − Σ₁(e) − Ch(e,f,g) − Kₜ − Wₜ
```

*bestimmt jeden Registerwert eindeutig. Verifiziert an 500 Parametrisierungen
über alle 64 Runden gegen die vorwärts protokollierte Zustandskette: null
Abweichungen.*

### 18.3 Wo die Bedingung entsteht

Nach der Reparametrisierung bleibt genau **eine** Bedingung übrig:
W₈…W₁₅ = Padding, 256 Bit.

| Schritt der Inversion | gewonnenes Wort | Status |
|---|---|---|
| 1–32 | W₄₇…W₁₆ | frei |
| **33** | **W₁₅** | erste prüfbare 32-Bit-Bedingung |
| 34–40 | W₁₄…W₈ | Padding-Zwang, je 32 Bit |
| 41–48 | W₇…W₀ | frei |

Früher Abbruch nach Schritt 33 statt 48 spart höchstens Faktor **1,45**. Das
ist die gesamte Ausbeute der Reparametrisierung an Rechenzeit; an der
Komplexität von 2²⁵⁶ ändert sie nichts.

### 18.4 Die linearisierte Padding-Bedingung — Bilanz negativ

Ersetzt man in der Rückwärtsrekursion die modulare Subtraktion durch XOR, wird
die Bedingung ein GF(2)-System und ist exakt lösbar.

| Größe | Wert |
|---|---|
| Unbekannte | 512 Bit (W₄₈…W₆₃) |
| Gleichungen | 256 Bit (W₈…W₁₅ = Padding) |
| Rang | **256** |
| Lösungsraum | 2²⁵⁶ |
| Probe im linearisierten Modell | exakt |

Diese exakten Lösungen, in **echter** modularer Arithmetik ausgewertet:

| | getroffene Padding-Bits von 256 |
|---|---|
| 2000 Lösungen des linearisierten Systems | 128,38 (50,15 %) |
| Kontrollgruppe, 2000 Zufallsparametrisierungen | 127,65 (49,86 %) |

**Kein Unterschied.** Auch aufgeschlüsselt nach Bitposition (0 bis 31) liegt
jede einzelne Position bei 49–51 % in beiden Gruppen. Die exakte Lösung des
linearisierten Systems ist genau so gut wie Raten.

*Methodischer Hinweis:* Ein erster Durchlauf lieferte dasselbe Ergebnis mit
einem fehlerhaften Löser (Rücksubstitution in absteigender statt aufsteigender
Pivotreihenfolge). Die Probe im linearisierten Modell schlug fehl und deckte
den Fehler auf. Ohne diese Probe wäre ein richtiges Ergebnis aus einer falschen
Rechnung entstanden.

### 18.5 Satz H — Reichweite der Linearisierung

**Satz H.** Das linearisierte Modell folgt der echten Rückwärts-Schedule
**genau einen Schritt weit.**

Gemessen bei identischem Schwanz, 3000 Zufallsfälle:

| Schritt | Wort | übereinstimmende Bits / 32 | Bit 0 korrekt |
|---|---|---|---|
| 1 | W₄₇ | 16,16 | **100,0 %** |
| 2 | W₄₆ | 15,97 | 49,6 % |
| 3 | W₄₅ | 16,01 | 50,3 % |
| 8 | W₄₀ | 15,95 | 49,9 % |
| 48 | W₀ | 15,96 | 52,2 % |

Zufallserwartung: 16,00 und 50,0 %.

Bit 0 ist in Schritt 1 exakt, weil die Subtraktion keinen Borrow **in** die
niedrigste Stelle erzeugt. Ab Schritt 2 ist auch das verschwunden.

**Ursache.** Im linearisierten System hängt Ausgabebit 0 von W₁₅ von **allen 32
Eingabe-Bitebenen** ab. Bei einer T-Funktion wären es genau eine. Die
Bitebenen-Kopplung entsteht dadurch, dass σ₀ und σ₁ Information nach unten
bewegen und damit verdorbene hohe Bits in niedrige Positionen ziehen.

### 18.6 Faktorieller Test — Schift, Rotation oder Übertrag?

Die naheliegende Vermutung, die Rechtsschifte (>>3, >>10) seien die Ursache,
ist **falsch**. Getestet wurden drei Bauarten von σ bei sonst identischer
Rekursion:

| Variante | Bauart | wirksame Eingabe-Bitebenen auf Ausgabeebene 0 |
|---|---|---|
| B1 | ROTR/ROTR/SHR — SHA-256 wie standardisiert | **32 von 32** |
| B2 | ROTR/ROTR/ROTR — Schift durch Rotation ersetzt | **32 von 32** |
| B3 | SHL/SHL/SHL — alles nach oben | **1** |

B1 und B2 sind ununterscheidbar. ROTR3 legt Bit 3 genauso auf Position 0 wie
SHR3; die beiden unterscheiden sich nur am oberen Rand. Entscheidend ist
ausschließlich die **Richtung**.

**Ebenenweiser Löser für die Padding-Bedingung.** Ebene p = 0…31 nacheinander,
je 17 Probeauswertungen, GF(2)-System aus 8 Gleichungen in 16 Unbekannten:

| Variante | getroffene Padding-Bits |
|---|---|
| B1 original | 122 / 256 (Zufall: 128) |
| B2 nur ROTR | 127 / 256 |
| **B3 nur SHL** | **256 / 256 — exakt gelöst** |

Für B3 unabhängig nachgeprüft: W₈…W₁₅ = 0x80000000, 0, …, 0x100, exakt das
Padding; der Schwanz ist nichttrivial (8 Wörter ungleich null); die
Vorwärtsprobe reproduziert ihn. Aufwand: **544 Schedule-Inversionen statt
2²⁵⁶**.

**Der Übertrag ist nicht das Hindernis.** Die XOR-Linearisierung trägt auch bei
B3 nichts (≈16 von 32 Bit, wie Zufall) — die Überträge sind dort genauso
vorhanden wie bei SHA-256. Trotzdem löst der Ebenen-Löser B3 exakt, weil
Überträge **aufwärts** fließen und der Löser aufwärts arbeitet: beim Bearbeiten
von Ebene p sind alle Überträge aus den Ebenen < p bereits festgelegt, also
Konstanten statt Unbekannte.

### 18.7 Variante T — vollständige Rückwärtslösung

**Aufbau.** Alle vier linearen Schichten (σ₀, σ₁, Σ₀, Σ₁) verwenden
Linksschifte statt Rechtsrotationen. Unverändert bleiben: acht Register,
64 Runden, Kₜ aus Kubikwurzeln, IV aus Quadratwurzeln, Ch/Maj, modulare
Addition, Padding. Damit ist die **gesamte** Kompressionsfunktion eine
T-Funktion.

| | |
|---|---|
| Unbekannte | W₄₈…W₆₃, 512 Bit |
| Bedingungen | W₈…W₁₅ = Padding (256 Bit) und Zustand₀ = IV (256 Bit) |
| Verfahren | Ebene p = 0…31, je 2¹⁶ Kandidaten vektorisiert, Rückverfolgung |

**Ergebnis:** Urbild gefunden, **161 besuchte Knoten**, Sekunden Rechenzeit.

```
Urbild (32 Byte):
1d590b9cb3447e749ee90a0cb89e1ed85447b1b0eee2cbc06dc17480b19a6a53
```

Padding exakt getroffen, Zielhash exakt getroffen — und **nicht** identisch mit
der Nachricht, aus der das Ziel erzeugt wurde. Es ist ein echtes Urbild, kein
Wiederfinden.

**Nebenbefund:** H = 0 ist unter Variante T unerreichbar; Ebene 0 ist sofort
leer. Die Linksschifte machen die Funktion nicht surjektiv. Das ist ein
Artefakt der Variante, kein Befund über SHA-256. Als Ziel wurde daher der
Variantenhash einer Zufallsnachricht gewählt, für den ein Urbild
nachweislich existiert.

### 18.8 Satz I — was eine Rechtsbewegung kostet

**Abwärtsreichweite:** um wie viele Bitebenen kann eine Änderung auf
Eingabeebene j eine Ausgabeebene p < j noch beeinflussen. Reichweite 0
bedeutet T-Funktion.

| Schritte | nur SHL | σ₀ rechts | σ₁ rechts | original |
|---|---|---|---|---|
| 1 | **0** | 18 | 19 | 19 |
| 2 | **0** | 24 | 19 | 28 |
| 3 | **0** | 30 | 19 | **31** |
| 4 | **0** | 31 | 19 | 31 |
| 8 | **0** | 31 | 19 | 31 |
| 48 | **0** | 31 | 31 | 31 |

Übersetzt in Kosten des ebenenweisen Lösers:

| Reichweite | Vorgehen | Kosten |
|---|---|---|
| 0 | 32 Ebenen einzeln | 32 · 2¹⁶ |
| w | w+1 Ebenen gemeinsam | 32 · 2^(16(w+1)) |
| 31 | alle Ebenen gemeinsam | 2⁵¹² |

**Satz I.** Eine einzige Rechtsrotation hebt die Abwärtsreichweite in **einem**
Anwendungsschritt von 0 auf 18–19 und damit die Kosten je Lösungsschritt von
2¹⁶ auf 2³⁰⁴. Nach drei Schritten ist die Reichweite maximal. Ein nutzbarer
Zwischenbereich existiert nicht.

Bemerkenswert ist die Asymmetrie: σ₁ allein bleibt bis Schritt 12 bei 19 und
sättigt erst über die volle Schedule; σ₀ allein sättigt nach vier Schritten.
Die Kopplung beider sättigt nach drei — schneller als jede Einzelkomponente.

### 18.9 Einordnung

**Was gewonnen ist.** Eine benannte, bezifferte Ursache:

> Überträge sind kein Hindernis. Sie fließen aufwärts und lassen sich aufwärts
> abarbeiten. Das Hindernis ist, dass σ und Σ Information **abwärts** bewegen,
> also gegen die Übertragsrichtung. Entfernt man diese Gegenrichtung bei sonst
> identischem Aufbau, kollabiert die Kompressionsfunktion von 2⁵¹² auf
> 32 · 2¹⁶ und ist rückwärts lösbar.

Das ist ein Entwurfsrationale-Befund derselben Art wie die Konstantenanalyse in
Abschnitt 5: die Wirkung einer Designentscheidung, isoliert und beziffert.

**Was nicht gewonnen ist.** Echtes SHA-256 ist unberührt; 2²⁵⁶ steht
unverändert. Die Messung schließt jedoch eine ganze Methodenfamilie sauber aus
— Hensel-Lifting, 2-adische Verfahren, T-Funktions-Ansätze nach
Klimov–Shamir. Nicht „hat nicht geklappt", sondern: scheitert nach einem
Anwendungsschritt, aus benennbarem Grund, mit Zahl.

**Präzisierung zu Abschnitt 8.1.** Dort steht, der Wahrscheinlichkeitsverlust
entstehe an den modularen Additionen und an Ch/Maj. Das ist für differentielle
Pfade richtig, für die algebraische Invertierung aber zu grob: Die Additionen
allein wären beherrschbar. Erst ihr Richtungskonflikt mit den linearen
Schichten macht sie teuer. Die linearen Schichten tragen also doch etwas bei —
nicht als Diffusionshindernis, sondern als **Richtungssperre**.

---

## 19. Nachprüfung des Dokuments

Unabhängige Nachrechnung ausgewählter Aussagen mit einer zweiten, getrennt
geschriebenen SHA-256-Implementierung (Konstanten aus den Primzahlen
hergeleitet, gegen `hashlib` an 200 Zufallseingaben validiert). Nicht die
Skripte des Anhangs nachgeführt, sondern parallel gerechnet.

### 19.1 Bestätigt

| Aussage | Prüfung | Ergebnis |
|---|---|---|
| Satz 1 (Padding) | direkt | ✓ |
| Satz 2 (W₁₆ = 0, und nur W₁₆) | 2000 Fälle | ✓ |
| Satz 3 (alle acht State₆₄-Werte) | direkt | ✓ |
| Satz 4 (0xfc08884d / 0x98c7e2a2) | direkt, Affinität stichprobenhaft | ✓ |
| Satz 5 (15 Ch- / 17 Maj-Bits) | direkt | ✓ |
| Satz 6 (Runde 7: genau ein Zustand) | 256 Eingaben | ✓ |
| Satz 8 (H₇ = e₆₁ + IV₇) | 500 Fälle | ✓ |
| Satz E (0 Kollisionen auf 256 Bit) | erschöpfend, 2¹⁶ | ✓ |
| Trunkierung 16/20/24/28/32 Bit | erschöpfend | 24092 / 1978 / 126 / 8 / 1 — exakt |
| 81 gültige Werte (≥ 10 Nullbits) | erschöpfend | ✓ |
| Satz 9, Bit 0 → 32.540 Monome, Grad 16 | Möbius über 2¹⁶ | ✓ |
| 9.7 AND-minimale cy- und Maj-Form | erschöpfend, 8 Belegungen | ✓ |
| Σ₁-Polynom, beide Inversen, Probe C·C⁻¹ ≡ 1 | direkt | ✓ |
| Rang aller vier Sigma-Funktionen | Gauß | 32/32 |
| 11.2 Minimalgewicht-Codewort | Einzelbit-Suche über 32 Positionen | **467**, 44 aktive Wörter, Profil 1/466 |

Das Minimalgewicht 467 wird vom Einzelbit an Position 15 in W₀ erreicht.

### 19.2 Abweichungen und Korrekturen

| Fundstelle | Art | Behandlung |
|---|---|---|
| Tabelle 12.1 | drei von vier Werten falsch | korrigiert, siehe 12.1 |
| Σ₀-Hexwert 0x20080400 | Tippfehler, Bit 29 statt 30 | korrigiert zu 0x40080400 in 7.4 und Messwerttabelle |
| Satz 11, Zuordnung der Nichtlinearitäten | sortiert statt zugeordnet | Tabelle ergänzt |
| Satz 9, Bereich 32.540–32.840 | Geltungsbereich zu weit angegeben | präzisiert |

Die Polynomschreibweise x³⁰ + x¹⁹ + x¹⁰ war stets korrekt, ebenso das Inverse
0xcbd1a68d; `ring_analyse.py` rechnet mit `1<<30`. Betroffen war nur die
Hex-Darstellung im Fließtext.

**Einordnung.** Keine der Korrekturen berührt eine Schlussfolgerung. Drei sind
Darstellungsfehler, eine ist eine Geltungsbereichsangabe. Bemerkenswert ist
allein Tabelle 12.1: dort wurde ein **falscher Kommentar im eigenen Skript** in
das Dokument übernommen, obwohl die Skriptausgabe daneben richtig war und
Abschnitt 8.1 den korrekten Wert bereits enthielt.


---

## 20. Fortschrittskurve für K1(r): Guess-and-Determine

Abschnitt 18 hat die Rückwärtsmechanik geklärt und die Sperre lokalisiert.
Offen blieb die quantitative Frage: **wie wächst der Aufwand pro zusätzlicher
Runde?** Dieser Abschnitt beantwortet sie für ein Guess-and-Determine-Verfahren.

Gemessen wird nicht Lösungszeit, sondern

> **g(r)** = Zahl der Nachrichtenbits, die geraten werden müssen, bis
> Constraint-Propagation den gesamten Rest bestimmt.

Die Kostenschranke ist 2^g(r) Propagationsläufe. Der Vorzug dieser Größe: Sie
ist auch dort noch messbar, wo eine vollständige Suche längst abbricht. Formal
ist g(r) die Größe eines starken Backdoors bezüglich Unit-Propagation.

### 20.1 Kodierung und ihre Verifikation

Tseitin-Kodierung der auf r Runden reduzierten Kompressionsfunktion, zwei
Modelle:

| Modell | freie Bits | Bemerkung |
|---|---|---|
| `block` | 512 (voller Block) | Instanzform der Literatur |
| `k1` | 256 (W₀…W₇, Padding fest) | das Objekt dieses Dokuments |

Jede modulare Addition ist bitgenau mit Übertragsvariablen modelliert
(s = a⊕b⊕c, cy = Maj(a,b,c)) — kein XOR-Ersatz, im Unterschied zur
Linearisierung aus 18.4.

Drei Korrektheitsnachweise, alle bestanden:

1. **Schattenauswertung.** Jede erzeugte Variable trägt den Bitwert einer
   bekannten Referenzrechnung mit. Geprüft für r ∈ {1, 4, 8, 16, 17, 18, 24, 64}
   in beiden Modellen: Ausgabe korrekt, **null unerfüllte Klauseln**. Die
   Referenzfunktion stimmt bei r = 64 mit `hashlib` überein.
2. **Propagationsvollständigkeit vorwärts.** Mit fixierten Nachrichtenbits
   bestimmt reine Unit-Propagation alle Variablen korrekt — bei r = 18 sind das
   15.058 von 15.058.
3. **Suchtest.** Ein eigener DPLL findet bei r = 4 mit 6 bzw. 10 freien Bits die
   Lösung in 10 bzw. 15 Knoten, W₀ exakt.

| r | Modell | Variablen | Klauseln |
|---|---|---|---|
| 18 | block | 16.486 | 69.494 |
| 18 | k1 | 15.058 | 64.067 |
| 64 | block | 75.186 | 328.856 |
| 64 | k1 | 71.480 | 312.988 |

### 20.2 Propagation ohne Raten

Was folgt allein aus dem Zielhash, ohne ein einziges geratenes Bit?

| r | Variablen | bestimmt | davon Nachrichtenbits |
|---|---|---|---|
| 9 | 7.427 | **7.427 (100 %)** | **256 / 256** |
| 12 | 9.786 | **9.786 (100 %)** | **256 / 256** |
| 16 | 12.969 | **12.969 (100 %)** | **256 / 256** |
| 18 | 15.058 | 3.279 (21,8 %) | 0 / 256 |
| 20 | 17.420 | 3.151 (18,1 %) | 0 / 256 |
| 24 | 22.167 | 3.051 (13,8 %) | 0 / 256 |

**Satz J (Linearzeitlösbarkeit von K1(r) für r ≤ 16).** Für r ≤ 16 bestimmt
reine Unit-Propagation aus dem Zielhash die gesamte Nachricht, ohne Suche.

*Beweis: konstruktiv und verifiziert. Für r = 9, 12, 16 ist die propagierte
Nachricht bitidentisch mit der erzeugenden, und die Nachrechnung trifft den
Zielhash. Propagation ist sofern korrekt, als sie nur implizierte Literale
ableitet; jede bestimmte Variable trägt damit zwangsläufig den Wert der
echten Lösung.*

*Ursache:* Rückwärts vom Ziel laufen die Runden mit konstantem Padding
(8–15) frei durch, vorwärts vom IV die Runden 0–7 mit W₀…W₇. Die beiden
Wellen treffen sich, und bei 256 freien Bits gegen 256 Bedingungen schließt
das System. Das freie Schedule-Fenster ist damit **exakt 16 Runden breit**.

Der Übergang bei r = 17 ist scharf: Dort greift die Expansion, die
Rückwärtswelle stößt auf ein unbekanntes W₁₆, und die Propagation bricht ab.
Ab r = 18 bestimmt sie **kein einziges** Nachrichtenbit mehr.

### 20.3 Die Kurve

Rateordnung wortweise, W₀ zuerst:

| r | 9–16 | 17 | 18 | 19 | 20 | 21 | 22 | ≥ 23 |
|---|---|---|---|---|---|---|---|---|
| **g(r)** | **0** | 64 | 96 | 128 | 160 | 192 | 224 | **256** |
| Kosten | 2⁰ | 2⁶⁴ | 2⁹⁶ | 2¹²⁸ | 2¹⁶⁰ | 2¹⁹² | 2²²⁴ | 2²⁵⁶ |
| Ersparnis | — | 2¹⁹² | 2¹⁶⁰ | 2¹²⁸ | 2⁹⁶ | 2⁶⁴ | 2³² | keine |

> **g(r) = 32 · (r − 15) für 17 ≤ r ≤ 23**, ohne einen einzigen Ausreißer.
> Wachstum exakt 32,0 Bit je Runde.

**Jede zusätzliche Runde kostet genau ein Nachrichtenwort.** Der
Freiheitsverbrauch ist ganzzahlig in Wörtern, nicht ungefähr wortgroß.

Bei r = 23 ist 2^g = 2²⁵⁶ erreicht — das Verfahren ist dort erschöpft. **Die
strukturelle Reichweite endet bei r = 22.**

### 20.4 Gibt es eine kleinere Ratemenge?

Drei Suchen nach einer besseren Menge, jede mit Kontrolle:

| Verfahren | r = 17 | r = 18 | r = 19 |
|---|---|---|---|
| wortweise, feste Reihenfolge | **64** | **96** | **128** |
| wortweise gierig | 64 | 96 | 128 |
| bitweise gierig (Stichprobe 48) | 73 | 105 | 132 |
| zufällige Auswahl (Kontrolle) | 254–256 | 254–256 | 255–256 |

Die wortweise gierige Suche findet stets dieselbe Reihenfolge (0, 1, 2, …) und
nie etwas Besseres. Die Zufallskontrolle zeigt, dass der Effekt real ist und
nicht aus der Zählweise stammt.

**Bitweise gierig ist schlechter, nicht besser.** Das ist der aufschlussreichste
Einzelbefund des Abschnitts, denn er hat einen benennbaren Grund:

> **Propagationsgewinne kommen in Wortquanten.** Ein halb geratenes Wort
> liefert fast nichts. Eine gierige Bitauswahl kann den Gewinn deshalb nicht
> kommen sehen und wählt in die falsche Richtung.

### 20.5 Was daraus für r > 16 folgt

Die Kurve nennt keinen Hebel. Sie **beziffert, was ein Hebel leisten müsste**:

> Um eine Runde zu gewinnen, müssen 32 Bit Freiheit zurückgewonnen werden.

Das ist keine vage Forderung, sondern eine Spezifikation — und sie erklärt
rückwirkend die Gestalt der publizierten Kryptanalyse. **Neutrale Bits** und
**Nachrichtenmodifikation** sind genau Techniken zur Freiheitsrückgewinnung;
**partielles Matching** in MITM-Angriffen reduziert stattdessen lokal die Zahl
der Bedingungen. Beides sind Antworten auf diese Rechnung. Was hier gemessen
wurde, ist der Wechselkurs.

**Einschränkungen, die die Zahl klein halten:**

- Praktisch nutzbar ist nur r ≤ 16. Schon 2⁶⁴ Propagationsläufe bei r = 17 sind
  unerreichbar. Die Kurve misst Struktur, nicht Machbarkeit.
- Die Instanzen sind konstruktionsgemäß erfüllbar, und geraten wird mit den
  Werten der bekannten Lösung. Es gibt daher keine Rückverfolgung; g(r) ist
  eine untere Schranke für den Suchaufwand, keine Laufzeit.
- Gemessen ist Guess-and-Determine mit Unit-Propagation. Ein CDCL-Solver mit
  Konfliktlernen kann sich anders verhalten; das zu prüfen ist die noch offene
  Hälfte von 17.3.

**Kein Ermüdungssignal.** Der Verbrauch von 32 Bit je Runde ist über sieben
Runden konstant. Es gibt keinen Hinweis auf eine Struktur, die bei höheren
Rundenzahlen nachgäbe.

### 20.6 Nächste messbare Frage

Wie viele **neutrale Bits** existieren bei r = 17 — also Bits, deren Kippen den
bereits determinierten Teil nicht zerstört? Findet man 32, ist eine Runde
gewonnen; findet man null, ist auch das eine Zahl. Mit derselben
Propagationsmaschine messbar, ohne externen Solver.

---

## 21. Neutrale Bits bei r = 17

Abschnitt 20 misst g(17) = 64: bei wortweiser Ratereihenfolge bestimmt
Unit-Propagation den gesamten Rest des Systems erst, nachdem W₀ und W₁
vollständig geraten sind. Offen blieb (Abschnitt 16), ob diese 64 Bits
tatsächlich alle nötig sind oder ob ein Teil davon **neutral** ist — also
sein Wert für das Schließen des Systems irrelevant wäre. Wäre das für 32 der
64 Bits der Fall, entspräche der scheinbare Sprung von g(16) = 0 auf
g(17) = 64 tatsächlich der glatten Rate von 32 Bit je Runde, die ab r = 18
gemessen wird — der Sprung wäre dann ein Artefakt eines zu groß geratenen
Backdoors, nicht die wahre Zahl.

### 21.1 Definition

Übertragen aus dem Begriff der neutralen Bits in der differentiellen
Kryptanalyse (Biham/Chen 2004) auf Guess-and-Determine statt auf ein
differentielles Merkmal:

> Ein geratenes Bit *i* ist **neutral**, wenn die Propagation bei allen
> übrigen 63 geratenen Bits auf ihrem Lösungswert **auch mit *i* auf dem
> geflippten Wert** konfliktfrei alle Variablen bestimmt.

Neutralität bedeutet: Bit *i* musste zwar irgendeinen Wert bekommen, aber
nicht notwendig den der Lösung — das System schließt so oder so. Ein
neutrales Bit zählt dann nicht zur eigentlich nötigen Ratemenge.

### 21.2 Messung

Werkzeug: dieselbe Propagationsmaschine aus Abschnitt 20
(`k1_propagation.py`, Zwei-Watch-Literale mit Rücknahme), kein externer
Solver. Für jede der 64 geratenen Positionen wird die volle
64-Bit-Zuweisung mit genau diesem einen Bit geflippt gegen die Maschine
geprüft, danach zurückgesetzt (`mark`/`undo`). Zehn unabhängige
Zufallsinstanzen (`k1_neutral_bits.py`).

| Seed | g(r) | neutrale Bits |
|---|---|---|
| 0–9 | 64 | **0** |

**Mittel über 10 Instanzen: 0,00 neutrale Bits von 64. Minimum 0, Maximum 0.**

### 21.3 Positivkontrolle

Dass „null neutrale Bits“ ein echter Befund und nicht ein Fehler in der
Rücknahme-Logik ist, zeigt die Gegenprobe: Bits **außerhalb** der
Ratemenge sind durch Propagation bereits erzwungen und müssen beim Flippen
sofort einen Konflikt auslösen.

| Seed | Stichprobe | Konflikt bei Flip |
|---|---|---|
| 0 | 20 | **20 / 20** |
| 1 | 20 | **20 / 20** |
| 2 | 20 | **20 / 20** |

Die Maschinerie unterscheidet forcierte von freien Bits also zuverlässig;
das Nullergebnis in 21.2 ist damit keine Artefakt-Erklärung wert.

### 21.4 Einordnung

**Satz K.** Bei r = 17 ist keines der 64 wortweise geratenen Nachrichtenbits
neutral bezüglich Unit-Propagation — geprüft einzeln, an zehn unabhängigen
Instanzen, ohne Ausnahme.

Damit ist die in Abschnitt 16 offene Frage entschieden: **g(17) = 64 ist die
tatsächliche Zahl, kein Messartefakt eines überdimensionierten Backdoors.**
Der Sprung von 0 auf 64 zwischen r = 16 und r = 17 ist real; die glatte Rate
von 32 Bit je Runde beginnt erst ab r = 17 → 18, nicht schon beim Übergang
in die rundenreduzierte Nachrichtenexpansion hinein.

**Reichweite der Aussage.** Geprüft ist Einzelbit-Neutralität — ob genau ein
Bit bei sonst unveränderter Lösung geflippt werden kann. Nicht geprüft ist
gemeinsame Neutralität mehrerer Bits gleichzeitig (ein Paar könnte
neutral sein, obwohl keines der beiden es einzeln ist). Nach Lehre 15
(Propagationsgewinne kommen in Wortquanten, nicht bitweise) ist das kein
naheliegender nächster Schritt, aber unbeauftragt logisch offen.

---

## Anhang: Programme

Alle Messungen sind mit den beiliegenden Skripten reproduzierbar.
Python 3.12, NumPy 2.4. Kein Netzzugang erforderlich. Die Skripte zu den
Abschnitten 18 und 19 sind eigenständig und setzen keine der übrigen Dateien
voraus; ihre SHA-256-Implementierungen sind jeweils separat gegen `hashlib`
validiert.

| Datei | Inhalt |
|---|---|
| `k1_test.py` | SHA-256-Eigenimplementierung, Konstantenherleitung aus Primzahlen, Validierung gegen hashlib, Lawineneffekt |
| `k1_runden.py` | Rundenweise Strukturanalyse, Ch/Maj-Determiniertheit |
| `k1_grad.py` | Algebraischer Grad via Cube-Summen |
| `k1_bruecke.py` | Konvergenztest der Gradmessung, ANF-Kostenrechnung |
| `k1_spezial.py` | Spezialisierte K1-Form, Verifikation, Operationszählung |
| `k1_kegel.py` | Ausgangs-Abhängigkeitskegel |
| `k1_dag.py` | Maschinelle Dead-Code-Elimination auf dem Operationsgraphen |
| `k1_1.py` | K1-1 Aufbau, vollständiger Durchlauf, Strukturprüfung |
| `k1_1_formel.py` | Exakte ANF via Möbius-Transformation, Kompressionstest |
| `k1_1_minimierung.py` | SOP-Logikminimierung mit Zufallskontrolle |
| `k1_1_ga.py` | Genetische Programmierung, Registermaschine |
| `k1_1_kontrolle.py` | Kapazitätsrechnung und Zufallslabel-Kontrolle |
| `k1_1_runde7.py` | Kompressionstest an Zwischenzuständen |
| `k1_1_schranken.py` | Abzählschranke, Beweisbarkeitsgrenzen |
| `k1_transform.py` | Affine Äquivalenz, Nichtlinearität, Bit-Permutationen |
| `k1_anf_approx.py` | Gradabschneidung, Koeffizientenvergleich |
| `k1_vergleich.py` | Vergleich der Varianten K1-1[p] mit Übertragbarkeitstest |
| `k1_opt.py` | Fitness-Optimierung, Benchmark alt/neu |
| `k1_gp_schnell.py` | GP mit optimierter Fitness, Holdout, Kontrolle |
| `konstanten.py` | Vier Konstantensätze, Lawine/Bias/Kollisionen |
| `rotation.py` | Rotationskryptanalyse, ARX-Wahrscheinlichkeiten |
| `konstanten_fein.py` | Feinvergleich mit 40 Zufallssätzen |
| `sqrt2_check.py` | Artefaktprüfung binär vs. dezimal |
| `k11_rotation.py` | Rotationsanalyse K1-1 vs. K1 |
| `k11_hintertuer.py` | Hintertür-Hypothese, identische Abtastung |
| `rot_kollision.py` | Erschöpfende Rotationskollisionssuche |
| `bitcoin_hashes.py` | Analyse der historischen Block-Hashes |
| `vorschlag.py` | Durchrechnung des Fest-Zielhash-Ansatzes |
| `runde_minimal.py` | Erschöpfende Minimalitätssuche für Ch und Maj |
| `andere_verdrahtung.py` | Zwei-Ketten-Darstellung, Rundenfusion, Verifikation |
| `andere_operationen.py` | Carry-less Multiplikation, Carry-Save-Zerlegung |
| `ring_analyse.py` | Ringstruktur, Invertierbarkeit, Rang und Kern |
| `cut_rewriting.py` | AIG-Konstruktion, strukturelles Hashing, Cut-Enumeration |
| `xaig.py` | XAIG mit nativen XOR, CSA-Vergleich, Gatterzählung |
| `mult_komplex.py` | Multiplikative Komplexität und AND-Tiefe |
| `beweise.py` | Sätze D, E, F: affine Bits, Kollisionsfreiheit, Injektivität |
| `groebner.py` | Quadratisches GF(2)-System, XL-Linearisierung, Gröbner-Komplexität |
| `k2_kegel.py` | Abhängigkeitskegel einzelner Ausgabebits |
| `wissensstand.py` | Abdeckung des Eingaberaums, Urbildstatistik |
| `kreuz_interferenz.py` | Orthogonale Testmatrix der Konstantensätze |
| `kausal.py` | Hochpräzise Kausalanalyse, gestaffelte Überlappung |
| `auftrag_1_2.py` | AND-minimale Formen, Kollisionsstatistiken |
| `verifikation.py` | XAIG-Simulation gegen hashlib, Signifikanzprüfung |
| `auftrag3.py` | Literaturabgleich, AND-Tiefe, Bristol-Fashion-Export |
| `cut_rewrite_min.py` | MC aller 4-Bit-Funktionen, Cut-Rewriting-Analyse |
| `k0.py` | K0: Strukturkarte, Lawineneffekt, Durchlauf |
| `expansion_code.py` | Expansionscode: Generatormatrix, erste Schranke |
| `expansion_max.py` | Ausgereizte Minimalgewichtsuche (ISD, Lee-Brickell) |
| `rx_analyse.py` | RX-Kryptanalyse, konstantes Fenster, Rundenkonstanten |
| `gueltige_suche.py` | Strukturtests auf gültigen K1-Eingaben |
| `hoehere_grade.py` | Gradabhängige Stichprobenkosten, Rang- und Differenztests |
| `k1_rueckwaerts.py` | Schedule-Inversion, Bijektion, Rückwärtstiefe, Verifikation (18.1–18.3) |
| `k1_rueck_linear.py` | Linearisierte Padding-Bedingung, GF(2)-Löser, Übertragsabweichung (18.4) |
| `k1_rueck_tiefe.py` | Reichweite der Linearisierung je Inversionsschritt (18.5) |
| `k1_sigma_varianten.py` | Faktorieller Test B1/B2/B3, ebenenweiser Löser (18.6) |
| `k1_variante_T_loeser.py` | Variante T, vollständige Rückwärtslösung mit Rückverfolgung (18.7) |
| `k1_abwaertsreichweite.py` | Abwärtsreichweite je Schrittzahl und Variante (18.8) |
| `k1_cnf.py` | Wiederverwendbarer CNF-Baustein der rundenreduzierten Kompression (20.1) |
| `k1_sat_kodierung.py` | Kodierung, drei Korrektheitsnachweise, DIMACS-Export (20.1) |
| `k1_sat_messlauf.py` | Messgerüst für externen CDCL-Solver, Exponentenanpassung (17.3) |
| `k1_propagation.py` | Unit-Propagation mit zwei beobachteten Literalen, mit Rücknahme |
| `k1_gnd_kurve.py` | Propagation ohne Raten, g(r) für drei Rateordnungen (20.2, 20.3) |
| `k1_gnd_vollstaendig.py` | Korrektheitsprüfung, vollständige Kurve, wortweise gierig (20.3, 20.4) |
| `k1_gnd_bitweise.py` | Bitweise gierige Suche mit Zufallskontrolle (20.4) |
| `k1_neutral_bits.py` | Neutrale-Bits-Test bei r = 17, mit Positivkontrolle (Abschnitt 21) |
| `nachpruefung_saetze.py` | Nachrechnung Sätze 1–8, Ringstruktur, AND-minimale Formen (19.1) |
| `nachpruefung_k1_1.py` | Nachrechnung K1-1 erschöpfend: Kollisionen, ANF, Nichtlinearität (19.1) |
| `nachpruefung_struktur.py` | Nachrechnung Satz 2/6, RX-Konstanten, Minimalgewicht 467 (19.1) |

### Zentrale Messwerte zum Nachprüfen

| Messung | Wert |
|---|---|
| ANF-Monome, K1-1 Bit 0 | 32.540 (Grad 16) |
| Nichtlinearität, K1-1[0x00] | 1924 |
| Operationen K1 / K1-1 | 861 / 747 von 952 |
| Fitness-Beschleunigung | 15,8× |
| z-Wert echte Konstanten | −0,04 |
| z-Wert Quadratwurzeln (Artefakt, s. 5.1) | −2,70 |
| z-Wert FIPS-Konstanten, Nachmessung | +0,455 |
| Bits je Messpunkt der Nachmessung | 12.288.000 |
| Differenz durch IV/K-Überlappung | 4,71 Sigma |
| ARX-Rotationswahrscheinlichkeit | 0,3749 (theoretisch 3/8) |
| DP der Addition, Δ = 0x80000000 | 1,0000 exakt |
| Ch minimal / Maj minimal | 3 / 4 Operationen (bewiesen) |
| Rundenoperationen Standard / Zwei-Ketten | 25 / 13 |
| Σ₀-Polynom / Inverses | 0x40080400 / 0xcbd1a68d |
| Σ₁-Polynom / Inverses | 0x04200080 / 0x6ab84f6c |
| Rang aller vier Sigma-Funktionen | 32/32 (bijektiv) |
| AIG-Basis / XAIG Gatterzahl (64 Runden) | 198.167 / 98.899 |
| Multiplikative Komplexität K1 (OR-Form) | 49.265 AND-Gatter |
| Multiplikative Komplexität K1 (AND-minimal) | **21.398** AND-Gatter |
| AND-Tiefe OR-Form / AND-minimal | 3.199 / 1.604 |
| AND-Tiefe je Runde (linear) | 25,1 |
| Bristol-Referenz vs. eigene Nachbildung | 22.573 / 22.573 (exakt) |
| Cut-Rewriting-Potenzial auf AND-minimalem Graphen | 5 von 21.398 (0,02 %) |
| Minimalgewicht Expansionscode | 467 (beide Dimensionen) |
| Kosten Grad-2-Beziehungstest auf Mining-Niveau | 2⁹⁴ Hashes |
| Obere Schranke Minimalabstand gültiger Eingaben | 28 (Kugelpackung) |
| AND-Gatter Runden 1–2 | 0 (beweist Affinität) |
| Affine Ausgabebits Runde 2 / Runde 3 | 256 / 0 |
| K1-1 Kollisionen auf 256 Bit | 0 (erschöpfend) |
| ANF-Monome K1-1, alle 256 Bits | 32.343–33.093, Mittel 32.765,7 |
| Schedule-Bijektion (W₄₈…W₆₃) ⟷ (W₀…W₁₅) | verifiziert, 2×2000 Fälle |
| deterministische Rückwärtstiefe von K1 | **64 von 64 Runden** |
| erste prüfbare Bedingung beim Rückwärtslauf | Schritt 33 von 48 (W₁₅) |
| Gewinn durch frühen Abbruch | Faktor 1,45 |
| linearisierte Padding-Lösung in echter Arithmetik | 128,4/256 gegen Kontrolle 127,7/256 |
| Reichweite der Linearisierung rückwärts | **1 Schritt** |
| Bitebenen-Kopplung B1 / B2 / B3 | 32 / 32 / **1** |
| Ebenenweiser Löser, Variante B3 | 256/256 exakt, 544 Inversionen |
| Variante T: Urbild gefunden | 161 Knoten, 32 Ebenen |
| Abwärtsreichweite nach 1 Rechtsrotation | 0 → 18–19 (Kosten 2¹⁶ → 2³⁰⁴) |
| K1(r) für r ≤ 16 | in Linearzeit lösbar, null geratene Bits |
| Breite des freien Schedule-Fensters | **16 Runden** |
| Ratemenge g(r), 17 ≤ r ≤ 23 | **32 · (r − 15)**, exakt |
| Freiheitsverbrauch je zusätzlicher Runde | **32 Bit = ein Nachrichtenwort** |
| strukturelle Reichweite von Guess-and-Determine | r = 22 |
| bitweise gierige Ratemenge, r = 17 | 73 (schlechter als 64) |
| Zufallskontrolle Ratemenge, r = 17 | 254–256 von 256 |
| CNF-Größe K1(18) / K1(64) | 15.058 / 71.480 Variablen |
