"""Teil 10: Vollstaendige Rueckwaertsloesung einer SHA-256-foermigen Funktion.

Variante T: alle vier linearen Schichten (sigma0, sigma1, Sigma0, Sigma1)
verwenden Linksschifte statt Rechtsrotationen. Alles Uebrige - acht Register,
Rundenzahl, Rundenkonstanten aus Kubikwurzeln, IV aus Quadratwurzeln,
Ch/Maj, modulare Addition, Padding - ist unveraendert.

Damit ist die gesamte Kompressionsfunktion eine T-Funktion: Ausgabe-Bitebene p
haengt nur von Eingabe-Bitebenen <= p ab. Geloest wird ebenenweise, p = 0..31,
mit Rueckverfolgung.

Unbekannte:  W48..W63           512 Bit
Bedingungen: W8..W15 = Padding  256 Bit
             Zustand_0 = IV     256 Bit
"""
import numpy as np, warnings
warnings.filterwarnings("ignore")
np.seterr(over='ignore')

M32 = 0xFFFFFFFF
def frac(x, n=32): return int((x - int(x)) * (1 << n))
def primes(k):
    ps, c = [], 2
    while len(ps) < k:
        if all(c % p for p in ps if p*p <= c): ps.append(c)
        c += 1
    return ps
P = primes(64)
IV = [frac(p**0.5) for p in P[:8]]
K  = [frac(p**(1/3.)) for p in P]
PAD = [0x80000000,0,0,0,0,0,0,0x00000100]

# ---- Variante T: alle Schichten mit Linksschift ----
shl = lambda x, n: x << np.uint32(n)
s0 = lambda x: shl(x,7)  ^ shl(x,18) ^ shl(x,3)
s1 = lambda x: shl(x,17) ^ shl(x,19) ^ shl(x,10)
Z0 = lambda x: shl(x,2)  ^ shl(x,13) ^ shl(x,22)
Z1 = lambda x: shl(x,6)  ^ shl(x,11) ^ shl(x,25)
Ch  = lambda e,f,g: (e & f) ^ (~e & g)
Maj = lambda a,b,c: (a&b) ^ (a&c) ^ (b&c)

def schedule_rueck(W_tail):
    W = {48+i: w for i, w in enumerate(W_tail)}
    for t in range(63, 15, -1):
        W[t-16] = W[t] - s1(W[t-2]) - W[t-7] - s0(W[t-15])
    return W

def runde_vor(st, t, Wt):
    a,b,c,d,e,f,g,h = st
    T1 = h + Z1(e) + Ch(e,f,g) + np.uint32(K[t]) + Wt
    T2 = Z0(a) + Maj(a,b,c)
    return [T1+T2, a, b, c, d+T1, e, f, g]

def runde_rueck(st, t, Wt):
    A,B,C,D,E,F,G,H = st
    a,b,c = B,C,D
    e,f,g = F,G,H
    T2 = Z0(a) + Maj(a,b,c)
    T1 = A - T2
    d  = E - T1
    h  = T1 - Z1(e) - Ch(e,f,g) - np.uint32(K[t]) - Wt
    return [a,b,c,d,e,f,g,h]

def kompress_vor(W16):
    W = list(W16)
    for t in range(16,64):
        W.append(np.uint32(s1(W[t-2]) + W[t-7] + s0(W[t-15]) + W[t-16]))
    st = [np.uint32(v) for v in IV]
    for t in range(64): st = runde_vor(st, t, W[t])
    return [int(np.uint32(x + np.uint32(y))) for x,y in zip(st, IV)], W

# ---- Selbsttest: Vorwaerts/Rueckwaerts konsistent ----
rng = np.random.default_rng(7)
W16 = [np.uint32(x) for x in rng.integers(0, 1<<32, 16, dtype=np.uint64)]
H, W = kompress_vor(W16)
st = [np.uint32(v) for v in IV]
for t in range(64): st = runde_vor(st, t, W[t])
zr = list(st)
for t in range(63,-1,-1): zr = runde_rueck(zr, t, W[t])
print("="*72)
print("TEIL 10  Variante T (alle Schichten Linksschift)")
print("="*72)
print(f"  Rundeninversion konsistent: {[int(x) for x in zr] == [int(v) for v in IV]}")
Wchk = schedule_rueck(W[48:64])
print(f"  Schedule-Inversion konsistent: "
      f"{all(int(np.uint32(Wchk[i])) == int(np.uint32(W[i])) for i in range(64))}")

# ---- Ziel festlegen: Hash einer bekannten Zufallsnachricht (garantiert erreichbar) ----
geheim = [np.uint32(x) for x in rng.integers(0, 1<<32, 8, dtype=np.uint64)]
W16z = geheim + [np.uint32(v) for v in PAD]
ZIEL_H, _ = kompress_vor(W16z)
st64 = [np.uint32((ZIEL_H[i] - IV[i]) & M32) for i in range(8)]
print(f"  Ziel H  = {[hex(v) for v in ZIEL_H[:4]]} ...")
print(f"  (Hash einer Zufallsnachricht unter Variante T; ein Urbild existiert also.)")
print(f"  Zustand_64 daraus eindeutig: kein Ratebedarf am Startpunkt.")

# ---- Ebenenweiser Loeser ----
C = np.arange(1<<16, dtype=np.uint32)
BITS = [((C >> np.uint32(w)) & np.uint32(1)) for w in range(16)]

def ebene_loesen(fixed, p):
    """alle Belegungen der 16 Unbekannten auf Ebene p, die alle 16 Bedingungen
    dieser Ebene erfuellen"""
    tail = [np.uint32(fixed[w]) | (BITS[w] << np.uint32(p)) for w in range(16)]
    W = schedule_rueck(tail)
    ok = np.ones(1<<16, dtype=bool)
    for k in range(8):
        ok &= (((W[8+k] >> np.uint32(p)) & 1) == ((PAD[k] >> p) & 1))
    if not ok.any(): return []
    st = [np.full(1<<16, v, dtype=np.uint32) for v in st64]
    for t in range(63, -1, -1):
        st = runde_rueck(st, t, W[t])
    for k in range(8):
        ok &= (((st[k] >> np.uint32(p)) & 1) == ((IV[k] >> p) & 1))
    return np.nonzero(ok)[0].tolist()

import sys
sys.setrecursionlimit(10000)
knoten = [0]
def dfs(fixed, p):
    if p == 32: return list(fixed)
    knoten[0] += 1
    kand = ebene_loesen(fixed, p)
    if p < 6 or len(kand) != 1:
        print(f"    Ebene {p:>2}: {len(kand)} Kandidat(en)")
    for cand in kand:
        neu = [fixed[w] | (((cand >> w) & 1) << p) for w in range(16)]
        r = dfs(neu, p+1)
        if r: return r
    return None

print()
print("  Ebenenweise Suche laeuft (32 Ebenen, je 2^16 Kandidaten vektorisiert)...")
loesung = dfs([0]*16, 0)
print(f"  besuchte Knoten: {knoten[0]}")

if loesung is None:
    print("  Keine Loesung fuer H = 0 (Erwartungswert war 1, Ausgang offen).")
else:
    tail = [np.uint32(v) for v in loesung]
    W = schedule_rueck(tail)
    W16f = [int(W[i]) for i in range(16)]
    Hf, _ = kompress_vor([np.uint32(v) for v in W16f])
    orig = [int(x) for x in geheim]
    print()
    print("  GEFUNDEN.")
    print(f"    W0..W7  = {[hex(v) for v in W16f[:8]]}")
    print(f"    W8..W15 = {[hex(v) for v in W16f[8:]]}")
    print(f"    Padding korrekt: {W16f[8:] == PAD}")
    print(f"    H = {[hex(v) for v in Hf]}")
    print(f"    Ziel getroffen: {Hf == ZIEL_H}")
    print(f"    identisch mit der urspruenglichen Nachricht: {W16f[:8] == orig}")
    nachricht = b''.join(v.to_bytes(4,'big') for v in W16f[:8])
    print(f"    Urbild (32 Byte): {nachricht.hex()}")
