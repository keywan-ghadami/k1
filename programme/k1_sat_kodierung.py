"""Werkzeugkalibrierung gegen die rundenreduzierte Preimage-Front (Abschnitt 17.3).

Erzeugt CNF-Instanzen fuer Preimage-Angriffe auf die auf r Runden reduzierte
SHA-256-Kompressionsfunktion und weist die Korrektheit der Kodierung nach,
bevor irgendein Solver laeuft.

Zwei Modelle:
  block  freier 512-Bit-Block, IV fest        (Setting der Literatur)
  k1     32-Byte-Nachricht, Padding fest      (das Objekt dieses Dokuments)

Ohne externe Abhaengigkeiten. Export im DIMACS-Format.
"""
import hashlib, itertools, os, sys, time

# ====================================================================== CNF
class CNF:
    """Tseitin-Kodierung mit mitlaufender Schattenauswertung.

    Jede erzeugte Variable traegt den konkreten Bitwert einer bekannten
    Referenzrechnung mit. Damit laesst sich am Ende pruefen, ob die
    Referenzloesung jede einzelne Klausel erfuellt."""
    def __init__(self):
        self.n = 0
        self.cls = []
        self.val = {}
        self.TRUE = self.newvar(1)
        self.cls.append([self.TRUE])

    def newvar(self, v):
        self.n += 1
        self.val[self.n] = v & 1
        return self.n

    def add(self, *lits):
        self.cls.append(list(lits))

    def lv(self, l):
        return self.val[abs(l)] ^ (1 if l < 0 else 0)

    # Konstanten
    def const(self, b):
        return self.TRUE if b else -self.TRUE
    def is_const(self, l):
        if l == self.TRUE:  return 1
        if l == -self.TRUE: return 0
        return None

    # --- Gatter ---
    def XOR(self, a, b):
        ca, cb = self.is_const(a), self.is_const(b)
        if ca is not None: return b if ca == 0 else -b
        if cb is not None: return a if cb == 0 else -a
        if a == b:  return self.const(0)
        if a == -b: return self.const(1)
        c = self.newvar(self.lv(a) ^ self.lv(b))
        self.add( a,  b, -c); self.add( a, -b,  c)
        self.add(-a,  b,  c); self.add(-a, -b, -c)
        return c

    def AND(self, a, b):
        ca, cb = self.is_const(a), self.is_const(b)
        if ca is not None: return self.const(0) if ca == 0 else b
        if cb is not None: return self.const(0) if cb == 0 else a
        if a == b:  return a
        if a == -b: return self.const(0)
        c = self.newvar(self.lv(a) & self.lv(b))
        self.add(-a, -b,  c); self.add( a, -c); self.add( b, -c)
        return c

    def MAJ(self, a, b, c):
        for x, y, z in ((a,b,c), (b,a,c), (c,a,b)):
            k = self.is_const(x)
            if k is not None:
                # Maj(1,y,z) = y OR z ; Maj(0,y,z) = y AND z
                return self.OR(y, z) if k == 1 else self.AND(y, z)
        m = self.newvar((self.lv(a)&self.lv(b)) ^ (self.lv(a)&self.lv(c)) ^ (self.lv(b)&self.lv(c)))
        self.add(-a,-b, m); self.add(-a,-c, m); self.add(-b,-c, m)
        self.add( a, b,-m); self.add( a, c,-m); self.add( b, c,-m)
        return m

    def OR(self, a, b):
        return -self.AND(-a, -b)

    def CH(self, e, f, g):          # g XOR (e AND (f XOR g))
        return self.XOR(g, self.AND(e, self.XOR(f, g)))

    # --- Wortebene, Index 0 = LSB ---
    def wconst(self, v):  return [self.const((v >> i) & 1) for i in range(32)]
    def wvar(self, v):    return [self.newvar((v >> i) & 1) for i in range(32)]
    def wval(self, w):    return sum(self.lv(l) << i for i, l in enumerate(w))

    def rotr(self, w, k): return [w[(i + k) % 32] for i in range(32)]
    def shr(self, w, k):  return [w[i + k] if i + k < 32 else self.const(0) for i in range(32)]
    def wxor(self, *ws):
        r = ws[0]
        for w in ws[1:]: r = [self.XOR(x, y) for x, y in zip(r, w)]
        return r

    def add32(self, x, y):
        out, c = [], self.const(0)
        for i in range(32):
            s = self.XOR(self.XOR(x[i], y[i]), c)
            c = self.MAJ(x[i], y[i], c) if i < 31 else c
            out.append(s)
        return out
    def addn(self, *ws):
        r = ws[0]
        for w in ws[1:]: r = self.add32(r, w)
        return r

# ============================================================ SHA-256-Teile
M32 = 0xFFFFFFFF
def frac(x, n=32): return int((x - int(x)) * (1 << n))
def primes(k):
    ps, c = [], 2
    while len(ps) < k:
        if all(c % p for p in ps if p*p <= c): ps.append(c)
        c += 1
    return ps
P  = primes(64)
IV = [frac(p**0.5) for p in P[:8]]
K  = [frac(p**(1/3.)) for p in P]
PAD = [0x80000000,0,0,0,0,0,0,0x00000100]

def sha_ref(W16, r):
    """Referenz: r-rundige Kompression, Feed-Forward. Reine Python-Arithmetik."""
    ro = lambda x,n: ((x>>n)|(x<<(32-n))) & M32
    s0 = lambda x: ro(x,7)^ro(x,18)^(x>>3)
    s1 = lambda x: ro(x,17)^ro(x,19)^(x>>10)
    W = list(W16)
    for t in range(16, r): W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16]) & M32)
    a,b,c,d,e,f,g,h = IV
    for t in range(r):
        T1 = (h + (ro(e,6)^ro(e,11)^ro(e,25)) + ((e&f)^(~e&g&M32)) + K[t] + W[t]) & M32
        T2 = ((ro(a,2)^ro(a,13)^ro(a,22)) + ((a&b)^(a&c)^(b&c))) & M32
        h,g,f,e,d,c,b,a = g,f,e,(d+T1)&M32,c,b,a,(T1+T2)&M32
    return [(x+y) & M32 for x,y in zip([a,b,c,d,e,f,g,h], IV)]

def baue(r, modus, W16_ref, ziel):
    """CNF fuer: finde Nachricht mit r-rundiger Kompression == ziel."""
    F = CNF()
    if modus == "block":
        W = [F.wvar(W16_ref[i]) for i in range(16)]
        frei = [l for w in W for l in w]
    else:                                   # k1: Padding fest
        W = [F.wvar(W16_ref[i]) for i in range(8)] + [F.wconst(v) for v in PAD]
        frei = [l for w in W[:8] for l in w]
    for t in range(16, r):
        s0 = F.wxor(F.rotr(W[t-15],7),  F.rotr(W[t-15],18), F.shr(W[t-15],3))
        s1 = F.wxor(F.rotr(W[t-2],17),  F.rotr(W[t-2],19),  F.shr(W[t-2],10))
        W.append(F.addn(s1, W[t-7], s0, W[t-16]))
    st = [F.wconst(v) for v in IV]
    for t in range(r):
        a,b,c,d,e,f,g,h = st
        S1 = F.wxor(F.rotr(e,6), F.rotr(e,11), F.rotr(e,25))
        S0 = F.wxor(F.rotr(a,2), F.rotr(a,13), F.rotr(a,22))
        ch = [F.CH(e[i],f[i],g[i]) for i in range(32)]
        mj = [F.MAJ(a[i],b[i],c[i]) for i in range(32)]
        T1 = F.addn(h, S1, ch, F.wconst(K[t]), W[t])
        T2 = F.add32(S0, mj)
        st = [F.add32(T1,T2), a, b, c, F.add32(d,T1), e, f, g]
    H = [F.add32(st[i], F.wconst(IV[i])) for i in range(8)]
    for i in range(8):
        for j in range(32):
            F.add(H[i][j] if (ziel[i] >> j) & 1 else -H[i][j])
    return F, frei, H

# ==================================================== 1  Korrektheitsnachweis
print("="*74)
print("1  KORREKTHEIT DER KODIERUNG")
print("="*74)
rng = __import__("random").Random(11)
alles_ok = True
for modus in ("block", "k1"):
    for r in (1, 4, 8, 16, 17, 18, 24, 64):
        W16 = [rng.getrandbits(32) for _ in range(16)]
        if modus == "k1": W16 = W16[:8] + PAD
        ziel = sha_ref(W16, r)
        F, frei, H = baue(r, modus, W16, ziel)
        # a) Schattenwerte reproduzieren die Referenz
        okH = [F.wval(H[i]) for i in range(8)] == ziel
        # b) jede Klausel ist unter der Referenzbelegung erfuellt
        bad = sum(1 for cl in F.cls if not any(F.lv(l) for l in cl))
        alles_ok &= okH and bad == 0
        if r in (18, 64):
            print(f"  {modus:>5} r={r:>2}: Vars {F.n:>7}  Klauseln {len(F.cls):>8}  "
                  f"Ausgabe korrekt {okH}  unerfuellte Klauseln {bad}")
print(f"  alle geprueften Instanzen konsistent: {alles_ok}")

# c) volle Runden gegen hashlib
msg = os.urandom(32)
W16 = [int.from_bytes((msg + b'\x80' + b'\x00'*23 + (256).to_bytes(8,'big'))[i:i+4], 'big')
       for i in range(0, 64, 4)]
h_ref = b''.join(v.to_bytes(4,'big') for v in sha_ref(W16, 64))
print(f"  Referenzfunktion r=64 == hashlib: {h_ref == hashlib.sha256(msg).digest()}")

# ==================================================== 2  Unit-Propagation
print()
print("="*74)
print("2  POSITIVKONTROLLE OHNE SUCHE: reine Unit-Propagation")
print("="*74)
def up(cls, nvar, units):
    """Unit-Propagation. Gibt Belegung oder None (Konflikt)."""
    watch = {}
    for i, cl in enumerate(cls):
        for l in cl: watch.setdefault(l, []).append(i)
    ass = {}
    stack = list(units)
    while stack:
        l = stack.pop()
        v, s = abs(l), (1 if l > 0 else 0)
        if v in ass:
            if ass[v] != s: return None
            continue
        ass[v] = s
        for i in watch.get(-l, ()):
            cl = cls[i]
            un, sat = None, False
            for m in cl:
                w = abs(m); si = 1 if m > 0 else 0
                if w in ass:
                    if ass[w] == si: sat = True; break
                else:
                    if un is not None: un = False; break
                    un = m
            if sat or un is False: continue
            if un is None: return None
            stack.append(un)
    return ass

W16 = [rng.getrandbits(32) for _ in range(8)] + PAD
for r in (8, 16, 18):
    ziel = sha_ref(W16, r)
    F, frei, H = baue(r, "k1", W16, ziel)
    ass = up(F.cls, F.n, [F.TRUE] + [l if F.lv(l) else -l for l in frei])
    voll = ass is not None and len(ass) == F.n
    ok = ass is not None and all(ass[abs(l)] ^ (1 if l < 0 else 0) == F.lv(l)
                                 for l in range(1, F.n+1))
    print(f"  k1 r={r:>2}: alle {F.n} Variablen durch Propagation bestimmt: {voll}, "
          f"Werte korrekt: {ok}")
print("  -> Die Kodierung ist propagationsvollstaendig in Vorwaertsrichtung.")
print("     Ein Solver, der das nicht sofort schafft, ist falsch angebunden.")

# ==================================================== 3  Suchtest
print()
print("="*74)
print("3  SUCHTEST: kleine Instanz tatsaechlich loesen (eigener DPLL)")
print("="*74)
def dpll_auf(cls, nvar, frei_vars, units):
    knoten = [0]
    def rek(units):
        knoten[0] += 1
        a = up(cls, nvar, units)
        if a is None: return None
        offen = [v for v in frei_vars if v not in a]
        if not offen: return a
        v = offen[0]
        for s in (1, 0):
            r = rek(units + [v if s else -v])
            if r is not None: return r
        return None
    return rek(units), knoten[0]

for k in (6, 10):
    W16 = [rng.getrandbits(32) for _ in range(8)] + PAD
    ziel = sha_ref(W16, 4)
    F, frei, H = baue(4, "k1", W16, ziel)
    fest = [l if F.lv(l) else -l for l in frei[k:]]
    freiv = [abs(l) for l in frei[:k]]
    t0 = time.time()
    a, kn = dpll_auf(F.cls, F.n, freiv, [F.TRUE] + fest)
    dt = time.time() - t0
    gef = None
    if a:
        gef = sum((a[abs(l)] ^ (1 if l < 0 else 0)) << i for i, l in enumerate(frei[:32]))
    print(f"  r=4, {k} freie Bits: Loesung gefunden {a is not None}, "
          f"{kn} Knoten, {dt:.2f}s, W0 = {gef if gef is None else hex(gef)} "
          f"(Soll {hex(W16[0])})")

# ==================================================== 4  Export
print()
print("="*74)
print("4  INSTANZEN FUER DEN EXTERNEN SOLVER")
print("="*74)
os.makedirs("cnf", exist_ok=True)
print(f"  {'Runden':>7} {'Modell':>7} {'Variablen':>11} {'Klauseln':>11} {'Datei':>26}")
for modus in ("block", "k1"):
    for r in (12, 14, 16, 17, 18, 19, 20, 21, 22, 24):
        W16 = [rng.getrandbits(32) for _ in range(16)]
        if modus == "k1": W16 = W16[:8] + PAD
        ziel = sha_ref(W16, r)
        F, frei, H = baue(r, modus, W16, ziel)
        name = f"cnf/preimage_{modus}_r{r:02d}.cnf"
        with open(name, "w") as fh:
            fh.write(f"c SHA-256 Preimage, {r} Runden, Modell {modus}\n")
            fh.write(f"c Ziel = Kompression einer bekannten Nachricht -> erfuellbar\n")
            fh.write(f"p cnf {F.n} {len(F.cls)}\n")
            for cl in F.cls: fh.write(" ".join(map(str, cl)) + " 0\n")
        print(f"  {r:>7} {modus:>7} {F.n:>11} {len(F.cls):>11} {name:>26}")

print()
print("  Alle Instanzen sind konstruktionsgemaess ERFUELLBAR (das Ziel ist der")
print("  Hash einer bekannten Nachricht). Gemessen wird also Loesungszeit,")
print("  nicht Unerfuellbarkeit. Fuer UNSAT-Kalibrierung: Zielbits zufaellig")
print("  waehlen - dann ist die Instanz mit hoher Wahrscheinlichkeit unloesbar.")

# ==================================================== 5  Echte Preimage-Instanzen
print()
print("="*74)
print("5  ECHTE PREIMAGE-INSTANZEN (Zufallsziel)")
print("="*74)
print("  Modell 'block': 512 freie Bits gegen 256 Bedingungen. Ein Urbild")
print("  existiert mit ueberwaeltigender Wahrscheinlichkeit; der Solver kennt")
print("  es nicht. Das ist die Instanzform der Literatur.")
print()
print(f"  {'Runden':>7} {'Variablen':>11} {'Klauseln':>11} {'Datei':>30}")
for r in (12, 14, 16, 17, 18, 19, 20, 21, 22, 24, 27, 30):
    W16 = [rng.getrandbits(32) for _ in range(16)]
    ziel = [rng.getrandbits(32) for _ in range(8)]
    F, frei, H = baue(r, "block", W16, ziel)
    name = f"cnf/echt_block_r{r:02d}.cnf"
    with open(name, "w") as fh:
        fh.write(f"c SHA-256 Preimage, {r} Runden, Zufallsziel\n")
        fh.write("c " + " ".join(f"{v:08x}" for v in ziel) + "\n")
        fh.write(f"p cnf {F.n} {len(F.cls)}\n")
        for cl in F.cls: fh.write(" ".join(map(str, cl)) + " 0\n")
    print(f"  {r:>7} {F.n:>11} {len(F.cls):>11} {name:>30}")
print()
print("  Erwartung: r <= 16 in Millisekunden (je Runde ein eigenes freies")
print("  Nachrichtenwort, keine Expansion). Ab r = 17 beginnt die Messung.")
