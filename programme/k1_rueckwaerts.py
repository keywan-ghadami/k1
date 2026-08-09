"""K1 rueckwaerts: Reparametrisierung ueber W48..W63.

Teil 1  Schedule-Inversion, Bijektion (W48..W63) <-> (W0..W15)
Teil 2  Rueckwaerts-Rundeninversion, Zaehlung der deterministischen Runden
Teil 3  Verifikation der gesamten Kette gegen hashlib
"""
import hashlib, random, os

M32 = 0xFFFFFFFF
rotr = lambda x, n: ((x >> n) | (x << (32-n))) & M32
S0 = lambda x: rotr(x,2) ^ rotr(x,13) ^ rotr(x,22)
S1 = lambda x: rotr(x,6) ^ rotr(x,11) ^ rotr(x,25)
s0 = lambda x: rotr(x,7) ^ rotr(x,18) ^ (x >> 3)
s1 = lambda x: rotr(x,17) ^ rotr(x,19) ^ (x >> 10)
Ch  = lambda e,f,g: (e & f) ^ (~e & g) & M32
Maj = lambda a,b,c: (a&b) ^ (a&c) ^ (b&c)

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
PAD = [0x80000000, 0,0,0,0,0,0, 0x00000100]      # W8..W15 bei 32-Byte-Eingabe

# ---------------------------------------------------------------- Teil 1
def expand(W16):
    """W0..W15 -> W0..W63 (vorwaerts, echte modulare Addition)"""
    W = list(W16)
    for t in range(16, 64):
        W.append((s1(W[t-2]) + W[t-7] + s0(W[t-15]) + W[t-16]) & M32)
    return W

def expand_inv(W_tail):
    """W48..W63 -> W0..W63 (rueckwaerts).
    W_{t-16} = W_t - s1(W_{t-2}) - W_{t-7} - s0(W_{t-15})
    Alle rechts stehenden Indizes sind > t-16, die Rekursion ist wohldefiniert."""
    W = {48+i: w for i, w in enumerate(W_tail)}
    for t in range(63, 15, -1):
        W[t-16] = (W[t] - s1(W[t-2]) - W[t-7] - s0(W[t-15])) & M32
    return [W[i] for i in range(64)]

print("="*70)
print("TEIL 1  Schedule-Inversion")
print("="*70)
ok_bij = True
for _ in range(2000):
    W16 = [random.getrandbits(32) for _ in range(16)]
    W = expand(W16)
    if expand_inv(W[48:64]) != W: ok_bij = False
print(f"  Bijektion (W48..W63) <-> (W0..W15), 2000 Zufallsfaelle: {ok_bij}")

# Gegenrichtung: zufaelliger Schwanz -> Kopf -> wieder Schwanz
ok_rt = True
for _ in range(2000):
    tail = [random.getrandbits(32) for _ in range(16)]
    if expand(expand_inv(tail)[:16])[48:64] != tail: ok_rt = False
print(f"  Rundlauf Schwanz -> Kopf -> Schwanz, 2000 Faelle:      {ok_rt}")
print(f"  -> Die Abbildung ist eine Bijektion auf 512 Bit. Jede Wahl von")
print(f"     W48..W63 legt W0..W15 eindeutig fest und umgekehrt.")

# ---------------------------------------------------------------- Teil 2
def runde_vor(st, t, Wt):
    a,b,c,d,e,f,g,h = st
    T1 = (h + S1(e) + Ch(e,f,g) + K[t] + Wt) & M32
    T2 = (S0(a) + Maj(a,b,c)) & M32
    return [(T1+T2)&M32, a, b, c, (d+T1)&M32, e, f, g]

def runde_rueck(st, t, Wt):
    """exakte Umkehrung von runde_vor, ohne Freiheitsgrad"""
    A,B,C,D,E,F,G,H = st                 # Zustand NACH Runde t
    a,b,c = B,C,D
    e,f,g = F,G,H
    T2 = (S0(a) + Maj(a,b,c)) & M32
    T1 = (A - T2) & M32
    d  = (E - T1) & M32
    h  = (T1 - S1(e) - Ch(e,f,g) - K[t] - Wt) & M32
    return [a,b,c,d,e,f,g,h]

print()
print("="*70)
print("TEIL 2  Rueckwaerts-Rundeninversion")
print("="*70)
det = 0
fehler = 0
for _ in range(500):
    tail = [random.getrandbits(32) for _ in range(16)]
    W = expand_inv(tail)
    st = list(IV)
    kette = [list(st)]
    for t in range(64):
        st = runde_vor(st, t, W[t]); kette.append(list(st))
    # rueckwaerts
    zr = list(st); tiefe = 0
    for t in range(63, -1, -1):
        zr = runde_rueck(zr, t, W[t])
        if zr != kette[t]: fehler += 1; break
        tiefe += 1
    det = max(det, tiefe)
print(f"  500 Zufallsparametrisierungen, Rueckwaertslauf vom Endzustand:")
print(f"    deterministisch invertierte Runden: {det} von 64")
print(f"    Abweichungen: {fehler}")
print(f"  -> Kein Verzweigungspunkt. Bei fester Wahl von W48..W63 ist der")
print(f"     gesamte Rueckwaertslauf eine Funktion, keine Suche.")

# ---------------------------------------------------------------- Teil 3
print()
print("="*70)
print("TEIL 3  Verifikation gegen hashlib")
print("="*70)
def k1_via_tail(tail):
    W = expand_inv(tail)
    st = list(IV)
    for t in range(64): st = runde_vor(st, t, W[t])
    return b''.join(((x+y) & M32).to_bytes(4,'big') for x,y in zip(st, IV))

ok_h = True
for _ in range(300):
    msg = os.urandom(32)
    m = msg + b'\x80' + b'\x00'*23 + (256).to_bytes(8,'big')
    W16 = [int.from_bytes(m[i:i+4],'big') for i in range(0,64,4)]
    tail = expand(W16)[48:64]
    if k1_via_tail(tail) != hashlib.sha256(msg).digest(): ok_h = False
print(f"  K1 ueber die Schwanz-Parametrisierung == hashlib, 300 Faelle: {ok_h}")

# Endzustand unter H = 0 (Satz 3) als Startpunkt des Rueckwaertslaufs
st64_H0 = [(~iv + 1) & M32 for iv in IV]
print(f"  Startzustand fuer H=0 (Satz 3): {[hex(x) for x in st64_H0[:3]]} ...")
print(f"  -> vollstaendig bekannt, kein Ratebedarf am Startpunkt.")

# ---------------------------------------------------------------- Teil 4
print()
print("="*70)
print("TEIL 4  Wo entstehen die Bedingungen?")
print("="*70)
print("  Reihenfolge der Schedule-Inversion (t = 63 abwaerts):")
print(f"  {'Schritt':>8} {'gewonnenes Wort':>16} {'Bedingung':>28}")
schritt = 0
for t in range(63, 15, -1):
    schritt += 1
    w = t-16
    if w == 15 or w == 8 or w == 7 or w == 0:
        bed = "Padding-Zwang (32 Bit)" if 8 <= w <= 15 else "frei"
        print(f"  {schritt:>8} {'W'+str(w):>16} {bed:>28}")
print(f"  -> Erste pruefbare 32-Bit-Bedingung (W15) nach Schritt 33 von 48.")
print(f"     Alle acht Padding-Woerter liegen nach Schritt 40 vor.")
print(f"     Frueher Abbruch spart damit hoechstens Faktor 48/33 = 1,45.")
