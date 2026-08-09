"""Teil 5-6: Wie teuer ist der Uebertrag an der Padding-Bedingung?

Die Padding-Bedingung W8..W15 = PAD ist die einzige Bedingung, die beim
Rueckwaertslauf ueber W48..W63 uebrig bleibt. In der LINEARISIERTEN Schedule
(+ -> XOR) ist sie ein GF(2)-System und exakt loesbar. Gemessen wird, wie weit
eine solche Loesung in der ECHTEN modularen Arithmetik traegt.
"""
import random

M32 = 0xFFFFFFFF
rotr = lambda x, n: ((x >> n) | (x << (32-n))) & M32
s0 = lambda x: rotr(x,7) ^ rotr(x,18) ^ (x >> 3)
s1 = lambda x: rotr(x,17) ^ rotr(x,19) ^ (x >> 10)
PAD = [0x80000000, 0,0,0,0,0,0, 0x00000100]

def inv_echt(tail):
    W = {48+i: w for i, w in enumerate(tail)}
    for t in range(63, 15, -1):
        W[t-16] = (W[t] - s1(W[t-2]) - W[t-7] - s0(W[t-15])) & M32
    return W

def inv_lin(tail):
    W = {48+i: w for i, w in enumerate(tail)}
    for t in range(63, 15, -1):
        W[t-16] = W[t] ^ s1(W[t-2]) ^ W[t-7] ^ s0(W[t-15])
    return W

# ---- Matrix des linearisierten Systems: 512 Unbekannte -> 256 Ausgabebits ----
def out_vec(W):                       # W8..W15 als 256-Bit-Zahl
    v = 0
    for k in range(8):
        v |= (W[8+k] & M32) << (32*k)
    return v

spalten = []
for j in range(512):
    tail = [0]*16
    tail[j//32] = 1 << (j % 32)
    spalten.append(out_vec(inv_lin(tail)))
ziel = 0
for k in range(8): ziel |= PAD[k] << (32*k)

# Zeilen aufbauen: Zeile i, Spalte j = Bit i von spalten[j]
rows = []
for i in range(256):
    r = 0
    for j in range(512):
        if (spalten[j] >> i) & 1: r |= 1 << j
    rows.append((r, (ziel >> i) & 1))

# Gauss ueber GF(2)
piv = {}
basis = []
for r, b in rows:
    for p, (pr, pb) in piv.items():
        if (r >> p) & 1: r ^= pr; b ^= pb
    if r == 0:
        assert b == 0, "System unloesbar"
        continue
    p = r.bit_length()-1
    piv[p] = (r, b)
rang = len(piv)
# Ruecksubstitution -> Partikulaerloesung
x = 0
for p in sorted(piv):
    r, b = piv[p]
    v = b
    rr = r & ~(1 << p)
    while rr:
        q = rr.bit_length()-1
        v ^= (x >> q) & 1
        rr &= ~(1 << q)
    if v: x |= 1 << p
# Nullraum-Basis (freie Variablen)
frei = [j for j in range(512) if j not in piv]
def loesung_mit(freibits):
    y = 0
    for idx, j in enumerate(frei):
        if (freibits >> idx) & 1: y |= 1 << j
    # abhaengige Bits nachziehen
    for p in sorted(piv):
        r, b = piv[p]
        v = b
        rr = r & ~(1 << p)
        while rr:
            q = rr.bit_length()-1
            v ^= (y >> q) & 1
            rr &= ~(1 << q)
        if v: y |= 1 << p
        else: y &= ~(1 << p)
    return y
def zu_tail(y): return [(y >> (32*i)) & M32 for i in range(16)]

print("="*70)
print("TEIL 5  Linearisiertes System der Padding-Bedingung")
print("="*70)
print(f"  Unbekannte: 512 Bit (W48..W63)")
print(f"  Gleichungen: 256 Bit (W8..W15 = Padding)")
print(f"  Rang: {rang}   Loesungsraum-Dimension: {512-rang}")
kontr = inv_lin(zu_tail(x))
print(f"  Probe: linearisierte Loesung trifft Padding exakt: "
      f"{[kontr[8+k] for k in range(8)] == PAD}")

# ---- Echte Arithmetik: wie viele der 256 Bit treffen? ----
print()
print("="*70)
print("TEIL 6  Uebertragsabweichung: Loesung in echter Arithmetik")
print("="*70)
N = 2000
def treffer(tail):
    W = inv_echt(tail)
    t, prob = 0, [0]*32
    for k in range(8):
        d = ~(W[8+k] ^ PAD[k]) & M32
        t += bin(d).count('1')
        for b in range(32): prob[b] += (d >> b) & 1
    return t, prob

sum_l, prof_l = 0, [0]*32
for _ in range(N):
    y = loesung_mit(random.getrandbits(len(frei)))
    t, p = treffer(zu_tail(y)); sum_l += t
    for b in range(32): prof_l[b] += p[b]
sum_r, prof_r = 0, [0]*32
for _ in range(N):
    t, p = treffer([random.getrandbits(32) for _ in range(16)]); sum_r += t
    for b in range(32): prof_r[b] += p[b]

print(f"  {N} Loesungen des linearisierten Systems:")
print(f"    getroffene Padding-Bits: {sum_l/N:.2f} von 256   "
      f"({100*sum_l/N/256:.2f} %)")
print(f"  Kontrollgruppe, {N} Zufallsparametrisierungen:")
print(f"    getroffene Padding-Bits: {sum_r/N:.2f} von 256   "
      f"({100*sum_r/N/256:.2f} %)")
print()
print("  Trefferquote nach Bitposition (0 = LSB, kein Uebertragseingang):")
print(f"  {'Bit':>4} {'linear.Loesung':>16} {'Zufall':>10}")
for b in [0,1,2,3,4,6,8,12,16,24,31]:
    print(f"  {b:>4} {100*prof_l[b]/(8*N):>15.1f}% {100*prof_r[b]/(8*N):>9.1f}%")

# ---- Warum keine bitebenenweise Loesung: Abhaengigkeit tiefer Ausgabebits ----
print()
print("="*70)
print("TEIL 7  Warum Hensel-Lifting/T-Funktion hier scheitert")
print("="*70)
abh = {}
for p in range(4):
    s = set()
    for j in range(512):
        if (spalten[j] >> p) & 1: s.add(j % 32)
    abh[p] = s
for p in range(4):
    print(f"  Ausgabebit {p} von W15 haengt von Eingabe-Bitebenen ab: "
          f"{sorted(abh[p])[:12]}{' ...' if len(abh[p])>12 else ''}")
print(f"  -> Ausgabebit 0 haengt von {len(abh[0])} der 32 Eingabe-Bitebenen ab.")
print("     Waere die Schedule eine T-Funktion, waere es genau {0}.")
print("     Ursache sind die Rechtsschifte in sigma0 (>>3) und sigma1 (>>10)")
print("     sowie die Rotationen: sie ziehen hohe Bits nach unten.")
