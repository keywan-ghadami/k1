"""Teil 11: Was kostet eine einzelne Rechtsbewegung?

Gemessen wird die ABWAERTSREICHWEITE: um wieviele Bitebenen kann eine
Aenderung auf Eingabeebene j eine Ausgabeebene p < j noch beeinflussen.
Reichweite 0 = T-Funktion = ebenenweise loesbar.
"""
import random
M32 = 0xFFFFFFFF
rotr = lambda x,n: ((x>>n)|(x<<(32-n))) & M32
shr  = lambda x,n: x >> n
shl  = lambda x,n: (x << n) & M32

def mk(art):
    if art == "SHL":
        return (lambda x: shl(x,7)^shl(x,18)^shl(x,3),
                lambda x: shl(x,17)^shl(x,19)^shl(x,10))
    if art == "ROTR":
        return (lambda x: rotr(x,7)^rotr(x,18)^shr(x,3),
                lambda x: rotr(x,17)^rotr(x,19)^shr(x,10))

def reichweite(s0, s1, schritte, versuche=300):
    """max(j - p) ueber alle beobachteten Einfluesse"""
    def lauf(tail):
        W = {48+i: w for i,w in enumerate(tail)}
        for k in range(schritte):
            t = 63 - k
            W[t-16] = (W[t] - s1(W[t-2]) - W[t-7] - s0(W[t-15])) & M32
        return [W[63-16-k] for k in range(schritte)]
    best = 0
    for _ in range(versuche):
        base = [random.getrandbits(32) for _ in range(16)]
        A = lauf(base)
        j = random.randrange(32); w = random.randrange(16)
        t2 = list(base); t2[w] ^= 1 << j
        B = lauf(t2)
        for a, b in zip(A, B):
            d = a ^ b
            if d:
                p = (d & -d).bit_length() - 1      # niedrigste geaenderte Ebene
                if j - p > best: best = j - p
    return best

print("="*72)
print("TEIL 11  Abwaertsreichweite in der Rueckwaerts-Schedule")
print("="*72)
print(f"  {'Schritte':>9} {'nur SHL':>10} {'sigma0 rechts':>15} {'sigma1 rechts':>15} {'original':>10}")
sL0, sL1 = mk("SHL"); sR0, sR1 = mk("ROTR")
for n in [1,2,3,4,6,8,12,48]:
    a = reichweite(sL0, sL1, n)
    b = reichweite(sR0, sL1, n)
    c = reichweite(sL0, sR1, n)
    d = reichweite(sR0, sR1, n)
    print(f"  {n:>9} {a:>10} {b:>15} {c:>15} {d:>10}")
print()
print("  Reichweite 0  -> T-Funktion, 32 Ebenen einzeln loesbar, Kosten 32 x 2^16")
print("  Reichweite w  -> w+1 Ebenen gemeinsam, Kosten 32 x 2^(16(w+1))")
print("  Reichweite 31 -> alle Ebenen gemeinsam, Kosten 2^512  (kein Gewinn)")
