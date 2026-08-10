"""V6 der Verifikation zu Abschnitt 22.4: Sind die Kodierungsvarianten
tatsaechlich die Verdrahtungen aus Abschnitt 9.1?

Der erste Messlauf zu 22.4 hat drei CNF-Varianten verglichen und ihre Groessen
implizit den Gatterzahlen aus 9.1 zugeordnet. Diese Zuordnung war unbelegt und
nachweislich falsch: 9.1 gibt fuer AND-minimal/OR-Uebertrag ein Verhaeltnis von
106.606/98.899 = 1,08 an, gemessen wurden 27.013/16.486 = 1,64. Ursachen:
(a) kein strukturelles Hashing in k1_cnf.CNF, (b) die 'aig'-Variante zerlegte
nur XOR, nicht die Maj, (c) andere Klammerung der Additionsketten.

Dieses Skript prueft vier Dinge:
  1. Rueckwaertskompatibilitaet - die Vorgabewerte erzeugen unveraendert die
     CNF, auf der die Abschnitte 20/21 beruhen.
  2. Korrektheit jeder Variante (Schattenauswertung, unerfuellte Klauseln).
  3. Gatterzahlen bei r=64 gegen die Zielwerte aus 9.1.
  4. Propagationsaequivalenz: g(17) je Variante. Nur wenn das uebereinstimmt,
     sind es dieselben Constraints in anderer Verpackung.
"""
import random, sys
sys.path.insert(0, ".")
from k1_cnf import baue, sha_ref, PAD
from k1_propagation import Prop

# Die drei Verdrahtungen aus Abschnitt 9.1, jetzt mit Hashing und der
# Klammerung aus auftrag_1_2.py, damit die Zahlen vergleichbar sind.
VARIANTEN = [
    ("aig",         dict(xor_nativ=False, carry_variante="or_gatter")),
    ("xaig_or",     dict(xor_nativ=True,  carry_variante="or_gatter")),
    ("xaig_andmin", dict(xor_nativ=True,  carry_variante="and_minimal")),
]
TREU = dict(hashing=True, assoz="baum")

# Zielwerte aus Abschnitt 9.1 (AND, XOR, gesamt), 64 Runden, Modell k1.
ZIEL_9_1 = {
    "aig":         (None,   None,   198167),   # dort arithmetisch abgeleitet
    "xaig_or":     (49265,  49634,   98899),
    "xaig_andmin": (21398,  85208,  106606),
}


def korrekt(r, modus, kw, seed):
    rng = random.Random(seed)
    W16 = [rng.getrandbits(32) for _ in range(16)]
    if modus == "k1": W16 = W16[:8] + PAD
    ziel = sha_ref(W16, r)
    F, frei, H = baue(r, modus, W16, ziel, **kw)
    okH = [F.wval(H[i]) for i in range(8)] == ziel
    bad = sum(1 for cl in F.cls if not any(F.lv(l) for l in cl))
    return F, okH, bad


def g_wert(r, kw, seed=0):
    """Ratemenge unter Unit-Propagation, wortweise - wie Abschnitt 20.3."""
    rng = random.Random(seed)
    W16 = [rng.getrandbits(32) for _ in range(8)] + PAD
    ziel = sha_ref(W16, r)
    F, frei, H = baue(r, "k1", W16, ziel, **kw)
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    geraten = 0
    for k in range(len(frei)):
        l = frei[k]
        if p.val(l) >= 0: continue
        geraten += 1
        if not p.entschieden(l if F.lv(l) else -l):
            return None, "Konflikt"
    return geraten, ("vollstaendig" if p.offen() == 0 else f"{p.offen()} offen")


print("=" * 78)
print("1  RUECKWAERTSKOMPATIBILITAET (Vorgabewerte = Basis der Abschnitte 20/21)")
print("=" * 78)
ERWARTET = {("block", 18): (16486, 69494), ("k1", 18): (15058, 64067),
            ("block", 64): (75186, 328856), ("k1", 64): (71480, 312988)}
alles = True
for (modus, r), (evar, ecls) in ERWARTET.items():
    F, okH, bad = korrekt(r, modus, {}, 11)
    ok = (F.n == evar and len(F.cls) == ecls and okH and bad == 0)
    alles &= ok
    print(f"  {modus:>5} r={r:<3} Vars {F.n:>6} (soll {evar})  "
          f"Klauseln {len(F.cls):>7} (soll {ecls})  {'OK' if ok else 'ABWEICHUNG'}")
print(f"  -> Vorgabeverhalten unveraendert: {alles}")

print()
print("=" * 78)
print("2  KORREKTHEIT DER VARIANTEN (9.1-treu: Hashing + Baum-Klammerung)")
print("=" * 78)
korr = True
for name, kw in VARIANTEN:
    zeilen = []
    for modus in ("block", "k1"):
        for r in (4, 17, 18):
            F, okH, bad = korrekt(r, modus, {**kw, **TREU}, 7)
            korr &= okH and bad == 0
            zeilen.append(okH and bad == 0)
    print(f"  {name:<12} {sum(zeilen)}/{len(zeilen)} Instanzen korrekt "
          f"(Ausgabe reproduziert, null unerfuellte Klauseln)")
print(f"  -> alle Varianten semantisch korrekt: {korr}")

print()
print("=" * 78)
print("3  GATTERZAHLEN r=64, Modell k1 - Abgleich mit Abschnitt 9.1")
print("=" * 78)
print(f"  {'Variante':<13} {'AND':>8} {'XOR':>8} {'gesamt':>8} | "
      f"{'Ziel 9.1':>9} {'Abw.':>8}")
for name, kw in VARIANTEN:
    F, okH, bad = korrekt(64, "k1", {**kw, **TREU}, 3)
    a, x = F.stat["and"], F.stat["xor"]
    ges = a + x + F.stat["maj"]
    za, zx, zg = ZIEL_9_1[name]
    abw = f"{100*(ges-zg)/zg:+.2f}%"
    zt = f"{za}/{zx}" if za else f"~{zg}"
    print(f"  {name:<13} {a:>8} {x:>8} {ges:>8} | {zg:>9} {abw:>8}   "
          f"(Ziel AND/XOR: {zt})")

print()
print("=" * 78)
print("4  PROPAGATIONSAEQUIVALENZ: g(17), Modell k1 (Abschnitt 20.3: g(17)=64)")
print("=" * 78)
for name, kw in [("vorgabe (20/21)", {})] + [(n, {**k, **TREU}) for n, k in VARIANTEN]:
    g, st = g_wert(17, kw)
    print(f"  {name:<16} g(17) = {g}   Propagation: {st}")

print()
print("=" * 78)
print("5  CNF-GROESSEN r=18, Modell block (Grundlage der 22.4-Messung)")
print("=" * 78)
print(f"  {'Variante':<13} {'Vars':>8} {'Klauseln':>10}")
groessen = {}
for name, kw in VARIANTEN:
    F, okH, bad = korrekt(18, "block", {**kw, **TREU}, 3)
    groessen[name] = (F.n, len(F.cls))
    print(f"  {name:<13} {F.n:>8} {len(F.cls):>10}")
r_or = groessen["xaig_andmin"][0] / groessen["xaig_or"][0]
print(f"\n  Verhaeltnis andmin/or = {r_or:.3f}  (9.1 erwartet 106606/98899 = 1.078)")
