"""Unabhaengige Nachrechnung ausgewaehlter Behauptungen.
Eigene SHA-256-Implementierung, gegen hashlib validiert."""
import hashlib, numpy as np

M32 = 0xFFFFFFFF
def rotr(x, n): return ((x >> n) | (x << (32 - n))) & M32

# --- Konstanten aus Primzahlen selbst herleiten (nicht abgeschrieben) ---
def frac_bits(x, n=32):
    return int((x - int(x)) * (1 << n))
def primes(k):
    ps, c = [], 2
    while len(ps) < k:
        if all(c % p for p in ps if p*p <= c): ps.append(c)
        c += 1
    return ps
P = primes(64)
IV = [frac_bits(p ** 0.5) for p in P[:8]]
K  = [frac_bits(p ** (1/3.)) for p in P]

S0 = lambda x: rotr(x,2) ^ rotr(x,13) ^ rotr(x,22)
S1 = lambda x: rotr(x,6) ^ rotr(x,11) ^ rotr(x,25)
s0 = lambda x: rotr(x,7) ^ rotr(x,18) ^ (x >> 3)
s1 = lambda x: rotr(x,17) ^ rotr(x,19) ^ (x >> 10)
Ch  = lambda e,f,g: (e & f) ^ (~e & g) & M32
Maj = lambda a,b,c: (a&b) ^ (a&c) ^ (b&c)

def expand(W):
    W = list(W)
    for t in range(16, 64):
        W.append((s1(W[t-2]) + W[t-7] + s0(W[t-15]) + W[t-16]) & M32)
    return W

def compress(W, iv=None, rounds=64, add_iv=True):
    iv = iv or IV
    a,b,c,d,e,f,g,h = iv
    W = expand(W)
    for t in range(rounds):
        T1 = (h + S1(e) + Ch(e,f,g) + K[t] + W[t]) & M32
        T2 = (S0(a) + Maj(a,b,c)) & M32
        h,g,f,e,d,c,b,a = g,f,e,(d+T1)&M32,c,b,a,(T1+T2)&M32
    st = [a,b,c,d,e,f,g,h]
    return [(x + y) & M32 for x,y in zip(st, iv)] if add_iv else st

def blocks32(msg32):
    """K1: 32-Byte-Nachricht -> genau ein Block, festes Padding"""
    m = msg32 + b'\x80' + b'\x00'*(64-32-1-8) + (256).to_bytes(8,'big')
    return [int.from_bytes(m[i:i+4],'big') for i in range(0,64,4)]

# ================= 0. Selbsttest gegen hashlib =================
import os
ok = all(bytes().join(x.to_bytes(4,'big') for x in compress(blocks32(m)))
         == hashlib.sha256(m).digest() for m in [os.urandom(32) for _ in range(200)])
print(f"[0] Eigenimplementierung == hashlib (200 Zufallseingaben): {ok}")
print(f"    IV/K aus Primzahlen hergeleitet, IV[0]={IV[0]:#010x} K[0]={K[0]:#010x}")

# ================= Satz 1: Padding =================
Wp = blocks32(b'\x00'*32)
print(f"\n[Satz 1] W8={Wp[8]:#010x} W9..W14={[hex(x) for x in Wp[9:15]]} W15={Wp[15]:#010x}")
print(f"         behauptet 0x80000000 / 0 / 0x00000100 -> "
      f"{Wp[8]==0x80000000 and all(x==0 for x in Wp[9:15]) and Wp[15]==0x100}")

# ================= Satz 3: Davies-Meyer-Inversion =================
soll = [0x95f61999,0x4498517b,0xc3910c8e,0x5ab00ac6,
        0xaef1ad81,0x64fa9774,0xe07c2655,0xa41f32e7]
ist  = [(~iv + 1) & M32 for iv in IV]
print(f"\n[Satz 3] State64 = ~IV+1 : {ist == soll}")
print(f"         {[hex(x) for x in ist[:4]]} ...")

# ================= Satz 4: Runde 0 affin in W0 =================
def runde0(W0):
    a,b,c,d,e,f,g,h = IV
    T1 = (h + S1(e) + Ch(e,f,g) + K[0] + W0) & M32
    T2 = (S0(a) + Maj(a,b,c)) & M32
    return (T1+T2) & M32, (d+T1) & M32
ca, ce = runde0(0)
diffs = {(runde0(w)[0]-w) & M32 for w in [0,1,7,0xdeadbeef,M32]}
print(f"\n[Satz 4] a1 = W0 + {ca:#010x}  (behauptet 0xfc08884d) -> {ca==0xfc08884d}")
print(f"         e1 = W0 + {ce:#010x}  (behauptet 0x98c7e2a2) -> {ce==0x98c7e2a2}")
print(f"         affin in W0 (Offset konstant ueber Stichprobe): {len(diffs)==1}")

# ================= Satz 5: determinierte Ch/Maj-Bits in Runde 1 =================
a,b,c,d,e,f,g,h = IV
# nach Runde 0: b=a_iv, c=b_iv, f=e_iv, g=f_iv
ch_det  = sum(1 for i in range(32) if ((IV[4]>>i)&1) == ((IV[5]>>i)&1))  # f,g = e_iv,f_iv
maj_det = sum(1 for i in range(32) if ((IV[0]>>i)&1) == ((IV[1]>>i)&1))  # b,c = a_iv,b_iv
print(f"\n[Satz 5] Ch-Bits determiniert: {ch_det}/32 (behauptet 15) -> {ch_det==15}")
print(f"         Maj-Bits determiniert: {maj_det}/32 (behauptet 17) -> {maj_det==17}")

# ================= Satz 8: Runden 61-63 irrelevant fuer H7 =================
import random
gleich = 0
for _ in range(500):
    m = os.urandom(32)
    W = blocks32(m)
    h64 = compress(W)[7]
    st61 = compress(W, rounds=61, add_iv=False)
    # h_64 = e_61 -> H7 = e_61 + IV[7]
    gleich += ((st61[4] + IV[7]) & M32) == h64
print(f"\n[Satz 8] H7 = e_61 + IV7 in {gleich}/500 Faellen -> {gleich==500}")

# ================= 9.7 AND-minimale Formen, erschoepfend =================
carry_ok = all((((a^c)&(b^c))^c) == ((a&b)|(a&c)|(b&c))
               for a in (0,1) for b in (0,1) for c in (0,1))
maj_ok   = all((((a^b)&(b^c))^b) == ((a&b)^(a&c)^(b&c))
               for a in (0,1) for b in (0,1) for c in (0,1))
print(f"\n[9.7] cy = ((a^c)&(b^c))^c  erschoepfend korrekt: {carry_ok}")
print(f"      Maj = ((a^b)&(b^c))^b  erschoepfend korrekt: {maj_ok}")

# ================= 8. Ringstruktur: Sigma-Inverse =================
def clmul_mod(a, b):  # zyklische Faltung mod x^32-1
    r = 0
    for i in range(32):
        if (b >> i) & 1:
            r ^= ((a << i) | (a >> (32-i))) & M32
    return r
def poly_of(func):   # Polynom = Bild des Einheitsvektors
    return func(1)
p0, p1 = poly_of(S0), poly_of(S1)
inv0, inv1 = 0xcbd1a68d, 0x6ab84f6c
print(f"\n[8] Sigma0-Polynom {p0:#010x} (behauptet 0x20080400) -> {p0==0x20080400}")
print(f"    Sigma1-Polynom {p1:#010x} (behauptet 0x04200080) -> {p1==0x04200080}")
print(f"    Probe C*C^-1 == 1 : S0 {clmul_mod(p0,inv0)==1}, S1 {clmul_mod(p1,inv1)==1}")
# Rang aller vier linearen Abbildungen
def rang(func):
    rows = [func(1 << i) for i in range(32)]
    r, piv = 0, []
    for bit in range(31, -1, -1):
        for i in range(r, 32):
            if (rows[i] >> bit) & 1:
                rows[r], rows[i] = rows[i], rows[r]
                for j in range(32):
                    if j != r and (rows[j] >> bit) & 1: rows[j] ^= rows[r]
                r += 1; break
    return r
print(f"    Raenge S0/S1/s0/s1: {[rang(f) for f in (S0,S1,s0,s1)]} (behauptet 32/32/32/32)")
