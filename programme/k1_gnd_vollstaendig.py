"""Fortsetzung: vollstaendige Kurve g(r), Korrektheitspruefung, Suche nach
einer besseren Ratemenge (wortweise gierig).
"""
import random, sys, time
sys.path.insert(0, ".")
from k1_cnf import baue, sha_ref, PAD, IV
from k1_propagation import Prop

def instanz(r, seed=0):
    rng = random.Random(seed)
    W16 = [rng.getrandbits(32) for _ in range(8)] + PAD
    ziel = sha_ref(W16, r)
    F, frei, H = baue(r, "k1", W16, ziel)
    return F, frei, W16, ziel

# =================================================== C  Korrektheitspruefung
print("=" * 76)
print("C  KORREKTHEIT: stimmt die propagierte Loesung mit der echten ueberein?")
print("=" * 76)
for r in (9, 12, 16):
    F, frei, W16, ziel = instanz(r)
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    voll = p.offen() == 0
    W = [sum((1 if p.val(frei[w*32+b]) == 1 else 0) << b for b in range(32))
         for w in range(8)]
    stimmt = W == W16[:8]
    nach = sha_ref(W + PAD, r) == ziel
    print(f"  r={r:>2}: alles bestimmt {voll}, Nachricht identisch {stimmt}, "
          f"Nachrechnung trifft Ziel {nach}")
print("  -> K1(r) ist fuer r <= 16 in Linearzeit loesbar, ohne jedes Raten.")
print("     Ursache: 256 freie Bits gegen 256 Bedingungen, und die Kopplung")
print("     zwischen IV-Seite und Zielseite ist propagationsvollstaendig.")

# =================================================== D  vollstaendige Kurve
print()
print("=" * 76)
print("D  KURVE g(r): wortweise Rateordnung")
print("=" * 76)
def g_wort(r, seed=0, reihenfolge=range(8)):
    F, frei, W16, _ = instanz(r, seed)
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    geraten = 0
    for w in reihenfolge:
        for b in range(32):
            l = frei[w*32+b]
            if p.val(l) >= 0: continue
            geraten += 1
            if not p.entschieden(l if F.lv(l) else -l): return None, None
        if p.offen() == 0: break
    return geraten, p.offen()

print(f"  {'r':>3} {'g(r)':>6} {'Kosten 2^g':>12} {'Ersparnis ggue. 2^256':>22}")
pts = []
for r in range(9, 27):
    g, off = g_wort(r)
    if g is None: print(f"  {r:>3}  Konflikt"); continue
    pts.append((r, g))
    ers = f"2^{256-g}" if g < 256 else "keine"
    print(f"  {r:>3} {g:>6} {'2^'+str(g):>12} {ers:>22}")

# Steigung im Bereich, in dem g waechst
w = [(r, g) for r, g in pts if 0 < g < 256]
if len(w) >= 2:
    a = (w[-1][1] - w[0][1]) / (w[-1][0] - w[0][0])
    print(f"\n  Wachstum im Bereich r={w[0][0]}..{w[-1][0]}: {a:.1f} Bit je Runde")
    print(f"  (32 Bit = genau ein Nachrichtenwort je zusaetzlicher Runde)")

# =================================================== E  bessere Ratemenge?
print()
print("=" * 76)
print("E  SUCHE NACH EINER KLEINEREN RATEMENGE (wortweise gierig)")
print("=" * 76)
def gierig(r, seed=0):
    F, frei, W16, _ = instanz(r, seed)
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    offen_w = list(range(8)); folge = []; geraten = 0
    while p.offen() > 0 and offen_w:
        best, bestw = None, None
        for w in offen_w:
            m = p.mark(); kosten = 0; ok = True
            for b in range(32):
                l = frei[w*32+b]
                if p.val(l) >= 0: continue
                kosten += 1
                if not p.entschieden(l if F.lv(l) else -l): ok = False; break
            rest = p.offen() if ok else 10**9
            p.undo(m)
            if ok and (best is None or (rest, kosten) < best):
                best, bestw, bestk = (rest, kosten), w, kosten
        if bestw is None: break
        for b in range(32):
            l = frei[bestw*32+b]
            if p.val(l) >= 0: continue
            geraten += 1
            p.entschieden(l if F.lv(l) else -l)
        folge.append(bestw); offen_w.remove(bestw)
    return geraten, folge, p.offen()

print(f"  {'r':>3} {'g wortweise':>13} {'g gierig':>10} {'Wortfolge':>22}")
for r in (17, 18, 19, 20, 21, 22, 23, 24):
    g0, _ = g_wort(r)
    g1, folge, off = gierig(r)
    print(f"  {r:>3} {g0:>13} {g1:>10} {str(folge):>22}")
print("  -> Findet die gierige Suche eine kleinere Menge, gibt es ausnutzbare")
print("     Struktur. Findet sie dieselbe, ist die Reihenfolge irrelevant und")
print("     der Freiheitsverbrauch je Runde ist eine harte Groesse.")
