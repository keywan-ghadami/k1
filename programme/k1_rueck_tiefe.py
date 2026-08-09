"""Teil 8: Reichweite des linearisierten Modells in der Rueckwaerts-Schedule."""
import random
M32 = 0xFFFFFFFF
rotr = lambda x,n: ((x>>n)|(x<<(32-n))) & M32
s0 = lambda x: rotr(x,7)^rotr(x,18)^(x>>3)
s1 = lambda x: rotr(x,17)^rotr(x,19)^(x>>10)

N = 3000
tref = {w: 0 for w in range(48)}          # uebereinstimmende Bits je Wort
lsb  = {w: 0 for w in range(48)}          # nur Bit 0
for _ in range(N):
    tail = [random.getrandbits(32) for _ in range(16)]
    A = {48+i: w for i,w in enumerate(tail)}   # echt
    B = dict(A)                                # linearisiert
    for t in range(63, 15, -1):
        A[t-16] = (A[t] - s1(A[t-2]) - A[t-7] - s0(A[t-15])) & M32
        B[t-16] = B[t] ^ s1(B[t-2]) ^ B[t-7] ^ s0(B[t-15])
        d = ~(A[t-16] ^ B[t-16]) & M32
        tref[t-16] += bin(d).count('1')
        lsb[t-16]  += d & 1

print("="*70)
print("TEIL 8  Wie tief traegt die Linearisierung rueckwaerts?")
print("="*70)
print(f"  {'Schritt':>7} {'Wort':>6} {'uebereinst. Bits/32':>21} {'Bit 0 korrekt':>15}")
schritt = 0
for t in range(63, 15, -1):
    schritt += 1
    w = t-16
    if schritt <= 8 or schritt in (10,12,16,20,24,33,40,48):
        print(f"  {schritt:>7} {'W'+str(w):>6} {tref[w]/N:>21.2f} "
              f"{100*lsb[w]/N:>14.1f}%")
print()
print("  Zufallserwartung bei voelliger Entkopplung: 16.00 / 50.0 %")
