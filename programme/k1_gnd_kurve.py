"""Fortschrittskurve fuer K1(r): Guess-and-Determine statt Brute Force.

Gemessen wird nicht Loesungszeit, sondern die Groesse der noetigen Rateменge:

  g(r) = Zahl der Nachrichtenbits, die geraten werden muessen, bis
         Constraint-Propagation den gesamten Rest bestimmt.

Kostenschranke des Angriffs: 2^g(r) Propagationslaeufe. Die Groesse ist auch
dort noch messbar, wo eine vollstaendige Suche laengst abbricht - genau das
macht sie zur Fortschrittskurve.

Leitfrage: Wie waechst g mit r, und was folgt daraus fuer r > 13?
"""
import random, sys, time
sys.path.insert(0, ".")
from k1_cnf import baue, sha_ref, PAD, IV

# ====================================================== Propagationsmaschine
class Prop:
    """Unit-Propagation mit zwei beobachteten Literalen, mit Ruecknahme."""
    def __init__(self, cls, n):
        self.n = n
        self.cls = [c for c in cls if len(c) > 1]
        self.units = [c[0] for c in cls if len(c) == 1]
        self.assign = [-1] * (n + 1)
        self.trail = []
        self.watch = {}
        for i, c in enumerate(self.cls):
            self.watch.setdefault(c[0], []).append(i)
            self.watch.setdefault(c[1], []).append(i)

    def val(self, l):
        a = self.assign[abs(l)]
        if a < 0: return -1
        return a if l > 0 else a ^ 1

    def enqueue(self, l):
        v = self.val(l)
        if v == 1: return True
        if v == 0: return False
        self.assign[abs(l)] = 1 if l > 0 else 0
        self.trail.append(l)
        return True

    def propagate(self, start):
        i = start
        while i < len(self.trail):
            l = self.trail[i]; i += 1
            wl = self.watch.get(-l)
            if not wl: continue
            rest = []
            for ci in wl:
                c = self.cls[ci]
                if c[0] == -l: c[0], c[1] = c[1], c[0]
                if self.val(c[0]) == 1:
                    rest.append(ci); continue
                for k in range(2, len(c)):
                    if self.val(c[k]) != 0:
                        c[1], c[k] = c[k], c[1]
                        self.watch.setdefault(c[1], []).append(ci)
                        break
                else:
                    rest.append(ci)
                    if not self.enqueue(c[0]):
                        self.watch[-l] = rest + wl[wl.index(ci)+1:]
                        return False
            self.watch[-l] = rest
        return True

    def start(self):
        for u in self.units:
            if not self.enqueue(u): return False
        return self.propagate(0)

    def mark(self): return len(self.trail)
    def undo(self, m):
        while len(self.trail) > m:
            self.assign[abs(self.trail.pop())] = -1

    def entschieden(self, l):
        m = self.mark()
        ok = self.enqueue(l) and self.propagate(m)
        return ok

    def offen(self):
        return sum(1 for v in range(1, self.n + 1) if self.assign[v] < 0)


# ====================================================== Instanzbau
def instanz(r, seed=0):
    rng = random.Random(seed)
    W16 = [rng.getrandbits(32) for _ in range(8)] + PAD
    ziel = sha_ref(W16, r)
    F, frei, H = baue(r, "k1", W16, ziel)
    return F, frei, W16


# ====================================================== Messung A
print("=" * 76)
print("A  PROPAGATION OHNE RATEN: was folgt allein aus dem Zielhash?")
print("=" * 76)
print(f"  {'r':>3} {'Variablen':>10} {'nach Propagation bestimmt':>26} {'davon Nachrichtenbits':>23}")
basis = {}
for r in (9, 10, 12, 16, 18, 20, 24):
    F, frei, W16 = instanz(r)
    p = Prop([list(c) for c in F.cls], F.n)
    t0 = time.time(); p.start(); dt = time.time() - t0
    best = F.n - p.offen()
    msg = sum(1 for l in frei if p.val(l) >= 0)
    basis[r] = (F.n, best, msg)
    print(f"  {r:>3} {F.n:>10} {best:>16} ({100*best/F.n:>5.1f} %) "
          f"{msg:>15} / 256   [{dt:.1f}s]")
print("  -> Der Zielhash allein legt nichts fest. Erwartet: Rueckwaertsrichtung")
print("     bricht an der ersten Uebertragskette ab.")

# ====================================================== Messung B
print()
print("=" * 76)
print("B  GUESS-AND-DETERMINE: g(r) fuer drei Rateordnungen")
print("=" * 76)

def ordnung(art, frei):
    if art == "wort":   # W0 Bit0..31, dann W1, ...
        return list(range(256))
    if art == "ebene":  # Bitebene 0 aller Woerter, dann Ebene 1, ...
        return [w*32 + b for b in range(32) for w in range(8)]
    if art == "hoch":   # Bitebene 31 abwaerts (gegen die Uebertragsrichtung)
        return [w*32 + b for b in range(31, -1, -1) for w in range(8)]
    raise ValueError

def g_messen(r, art, seed=0):
    F, frei, W16 = instanz(r, seed)
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    idx = ordnung(art, frei)
    geraten = 0
    for k in idx:
        l = frei[k]
        if p.val(l) >= 0: continue          # schon bestimmt: gratis
        geraten += 1
        lit = l if F.lv(l) else -l          # Wert der bekannten Loesung
        if not p.entschieden(lit):
            return None, None, None         # Konflikt (sollte nicht auftreten)
    return geraten, p.offen(), F.n

print(f"  {'r':>3} {'wortweise':>12} {'ebenenweise':>13} {'hohe Ebenen':>13} {'Rest offen':>12}")
kurve = {}
for r in (9, 10, 11, 12, 13, 14, 16, 18, 20):
    zeile = []
    for art in ("wort", "ebene", "hoch"):
        g, off, n = g_messen(r, art)
        zeile.append(g)
    kurve[r] = zeile
    print(f"  {r:>3} {zeile[0]:>12} {zeile[1]:>13} {zeile[2]:>13} {off:>12}")
print("  (g = geratene Nachrichtenbits; 256 = kein Gewinn gegenueber Erschoepfung)")
