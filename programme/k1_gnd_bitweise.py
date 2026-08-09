"""F: Laesst sich die Ratemenge auf Bitebene unter 32(r-15) druecken?

Die wortweise gierige Suche (Messung E) fand nichts Besseres. Sie arbeitet
aber nur auf Wortgranularitaet. Hier wird bitweise gierig gesucht: in jedem
Schritt wird unter einer Stichprobe noch freier Bits dasjenige gewaehlt, das
die meisten weiteren Variablen bestimmt.

Findet die Suche deutlich weniger als 32(r-15) Bits, existiert ausnutzbare
Struktur. Findet sie dieselbe Zahl, ist der Freiheitsverbrauch je Runde eine
harte Groesse und kein Artefakt der Reihenfolge.
"""
import random, sys, time
sys.path.insert(0, ".")
from k1_cnf import baue, sha_ref, PAD
from k1_propagation import Prop

def instanz(r, seed=0):
    rng = random.Random(seed)
    W16 = [rng.getrandbits(32) for _ in range(8)] + PAD
    return baue(r, "k1", W16, sha_ref(W16, r))

def bitweise_gierig(r, stichprobe=48, seed=0):
    F, frei, H = instanz(r, seed)
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    rng = random.Random(99)
    gewaehlt, versuche = [], 0
    while p.offen() > 0:
        kand = [k for k in range(256) if p.val(frei[k]) < 0]
        if not kand: break
        probe = kand if len(kand) <= stichprobe else rng.sample(kand, stichprobe)
        best, bestk = None, None
        for k in probe:
            l = frei[k]; lit = l if F.lv(l) else -l
            m = p.mark()
            ok = p.entschieden(lit)
            rest = p.offen() if ok else -1
            p.undo(m); versuche += 1
            if ok and (best is None or rest < best):
                best, bestk = rest, k
        if bestk is None: return None, versuche
        l = frei[bestk]
        p.entschieden(l if F.lv(l) else -l)
        gewaehlt.append(bestk)
    return len(gewaehlt), versuche

print("=" * 76)
print("F  BITWEISE GIERIGE SUCHE NACH EINER KLEINEREN RATEMENGE")
print("=" * 76)
print(f"  {'r':>3} {'32(r-15)':>10} {'wortweise':>11} {'bitweise gierig':>17} {'Probeschritte':>15} {'Zeit':>8}")
for r in (17, 18, 19):
    t0 = time.time()
    g, v = bitweise_gierig(r)
    dt = time.time() - t0
    print(f"  {r:>3} {32*(r-15):>10} {'—':>11} {g:>17} {v:>15} {dt:>7.0f}s")
print()
print("  Kontrolle: dieselbe Suche mit zufaelliger statt gieriger Auswahl")
def zufall(r, seed=0):
    F, frei, H = instanz(r, seed)
    p = Prop([list(c) for c in F.cls], F.n); p.start()
    rng = random.Random(seed + 5); g = 0
    while p.offen() > 0:
        kand = [k for k in range(256) if p.val(frei[k]) < 0]
        if not kand: break
        k = rng.choice(kand); l = frei[k]; g += 1
        if not p.entschieden(l if F.lv(l) else -l): return None
    return g
for r in (17, 18, 19):
    vals = [zufall(r, s) for s in range(3)]
    print(f"  r={r:>2}: zufaellige Auswahl {vals}, Soll {32*(r-15)}")
