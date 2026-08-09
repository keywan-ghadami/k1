"""Teil 9: Woher stammt die Sperre - Uebertrag, Rotation oder Schift?

Faktorieller Aufbau. Die Schedule-Rueckwaertsrekursion bleibt in allen
Varianten identisch:
    W_{t-16} = W_t - s1(W_{t-2}) - W_{t-7} - s0(W_{t-15})   mod 2^32
Variiert wird ausschliesslich die Bauart von sigma0/sigma1.
"""
import random
M32 = 0xFFFFFFFF
rotr = lambda x,n: ((x>>n)|(x<<(32-n))) & M32
shr  = lambda x,n: x >> n
shl  = lambda x,n: (x << n) & M32
PAD = [0x80000000,0,0,0,0,0,0,0x00000100]

VAR = {
  # Name: (sigma0, sigma1, Beschreibung)
  "B1 original":  (lambda x: rotr(x,7)^rotr(x,18)^shr(x,3),
                   lambda x: rotr(x,17)^rotr(x,19)^shr(x,10),
                   "ROTR/ROTR/SHR  - SHA-256 wie standardisiert"),
  "B2 nur ROTR":  (lambda x: rotr(x,7)^rotr(x,18)^rotr(x,3),
                   lambda x: rotr(x,17)^rotr(x,19)^rotr(x,10),
                   "ROTR/ROTR/ROTR - Schift durch Rotation ersetzt"),
  "B3 nur SHL":   (lambda x: shl(x,7)^shl(x,18)^shl(x,3),
                   lambda x: shl(x,17)^shl(x,19)^shl(x,10),
                   "SHL/SHL/SHL    - alles nach oben, T-Funktion"),
}

def inv(tail, s0, s1, xor=False):
    W = {48+i: w for i,w in enumerate(tail)}
    for t in range(63, 15, -1):
        if xor: W[t-16] = W[t] ^ s1(W[t-2]) ^ W[t-7] ^ s0(W[t-15])
        else:   W[t-16] = (W[t] - s1(W[t-2]) - W[t-7] - s0(W[t-15])) & M32
    return W

# ---------------------------------------------------------------- 9.1
print("="*72)
print("9.1  Bitebenen-Abhaengigkeit: haengt Ausgabeebene p von Eingabeebene j>p ab?")
print("="*72)
print("  Getestet: Ausgabebit 0 von W8..W15, Eingabebit-Ebene j gekippt.")
print(f"  {'Variante':>14} {'wirksame Eingabeebenen auf Ausgabeebene 0':>44}")
for name,(s0,s1,_) in VAR.items():
    wirk = set()
    for _ in range(40):
        base = [random.getrandbits(32) for _ in range(16)]
        A = inv(base, s0, s1)
        for j in range(32):
            for w in range(16):
                t2 = list(base); t2[w] ^= 1 << j
                B = inv(t2, s0, s1)
                if any(((A[8+k]^B[8+k]) & 1) for k in range(8)):
                    wirk.add(j); break
    lo = sorted(wirk)
    print(f"  {name:>14}   {len(lo):>2} Ebenen: {lo[:10]}{' ...' if len(lo)>10 else ''}")
print("  T-Funktion waere: genau {0}.")

# ---------------------------------------------------------------- 9.2
print()
print("="*72)
print("9.2  Reichweite der Linearisierung (echt vs. XOR, identischer Schwanz)")
print("="*72)
N = 1500
print(f"  {'Variante':>14} {'Schritt 1':>12} {'Schritt 2':>12} {'Schritt 8':>12} {'Schritt 48':>12}")
for name,(s0,s1,_) in VAR.items():
    tr = {w:0 for w in range(48)}
    for _ in range(N):
        tail = [random.getrandbits(32) for _ in range(16)]
        A = inv(tail, s0, s1); B = inv(tail, s0, s1, xor=True)
        for w in range(48):
            tr[w] += bin(~(A[w]^B[w]) & M32).count('1')
    g = lambda schritt: tr[64-16-schritt]/N
    print(f"  {name:>14} {g(1):>11.2f} {g(2):>11.2f} {g(8):>11.2f} {g(48):>11.2f}")
print("  (uebereinstimmende Bits von 32; Zufallserwartung 16.00)")

# ---------------------------------------------------------------- 9.3
print()
print("="*72)
print("9.3  Bitebenenweiser Loeser fuer die Padding-Bedingung W8..W15 = PAD")
print("="*72)
print("  Verfahren: Ebene p = 0,1,...,31 nacheinander. Bei einer T-Funktion")
print("  ist die Ausgabe auf Ebene p affin in den 16 Unbekannten dieser Ebene,")
print("  sobald die Ebenen < p fixiert sind. 17 Probeauswertungen je Ebene.")
print()

def loese_ebenenweise(s0, s1):
    tail = [0]*16
    for p in range(32):
        # affines Modell der Ausgabeebene p in den 16 Unbekannten dieser Ebene
        A0 = inv(tail, s0, s1)
        const = [ (A0[8+k] >> p) & 1 for k in range(8) ]
        cols = []
        for w in range(16):
            t2 = list(tail); t2[w] ^= 1 << p
            A = inv(t2, s0, s1)
            cols.append([ ((A[8+k] >> p) & 1) ^ const[k] for k in range(8) ])
        ziel = [ ((PAD[k] >> p) & 1) ^ const[k] for k in range(8) ]
        # 8 Gleichungen, 16 Unbekannte, GF(2)
        rows = [ (sum(cols[w][k] << w for w in range(16)), ziel[k]) for k in range(8) ]
        piv = {}
        for r,b in rows:
            for q,(pr,pb) in piv.items():
                if (r>>q)&1: r ^= pr; b ^= pb
            if r == 0:
                if b: return None, p          # Ebene unloesbar
                continue
            piv[r.bit_length()-1] = (r,b)
        x = 0
        for q in sorted(piv):
            r,b = piv[q]; v = b; rr = r & ~(1<<q)
            while rr:
                u = rr.bit_length()-1; v ^= (x>>u)&1; rr &= ~(1<<u)
            if v: x |= 1<<q
        for w in range(16):
            if (x>>w)&1: tail[w] |= 1<<p
    return tail, None

for name,(s0,s1,desc) in VAR.items():
    tail, fehl = loese_ebenenweise(s0, s1)
    if tail is None:
        print(f"  {name:<14} Abbruch auf Ebene {fehl}")
        continue
    W = inv(tail, s0, s1)
    got = [W[8+k] for k in range(8)]
    korrekt = sum(bin(~(got[k]^PAD[k]) & M32).count('1') for k in range(8))
    print(f"  {name:<14} {korrekt:>3}/256 Padding-Bits getroffen   "
          f"{'EXAKT GELOEST' if korrekt==256 else '(Zufall waere 128)'}")
    if korrekt == 256:
        print(f"                 Loesung W48..W51 = "
              f"{[hex(t) for t in tail[:4]]} ...")
        print(f"                 Aufwand: 32 Ebenen x 17 Auswertungen = 544 "
              f"Schedule-Inversionen")
