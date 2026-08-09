"""Rotationskollisionen in K1-1: erschoepfend ueber alle 65.536 Eingaben.
Traegt die Restsymmetrie bis in hoehere Runden?
"""
import random, math
import numpy as np
MASK=0xFFFFFFFF
def rotr(x,n): return ((x>>n)|(x<<(32-n)))&MASK
def rotl(x,n): return ((x<<n)|(x>>(32-n)))&MASK
def S0(x): return rotr(x,2)^rotr(x,13)^rotr(x,22)
def S1(x): return rotr(x,6)^rotr(x,11)^rotr(x,25)
def s0(x): return rotr(x,7)^rotr(x,18)^(x>>3)
def s1(x): return rotr(x,17)^rotr(x,19)^(x>>10)
def Ch(e,f,g): return (e&f)^((~e&MASK)&g)
def Maj(a,b,c): return (a&b)^(a&c)^(b&c)
def icbrt(n):
    lo,hi=0,1
    while hi**3<=n: hi*=2
    while lo<hi:
        m=(lo+hi+1)//2
        if m**3<=n: lo=m
        else: hi=m-1
    return lo
def primes(n):
    p=[];c=2
    while len(p)<n:
        if all(c%q for q in p if q*q<=c): p.append(c)
        c+=1
    return p
P=primes(64)
IV=[math.isqrt(p*(1<<64))&MASK for p in primes(8)]
K=[icbrt(p*(1<<96))&MASK for p in P]
PAD=[0x80000000,0,0,0,0,0,0,0x00000100]

def kompress(W16,runden,iv):
    W=list(W16)
    for t in range(16,runden):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK)
    a,b,c,d,e,f,g,h=iv
    for t in range(runden):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK
        T2=(S0(a)+Maj(a,b,c))&MASK
        h,g,f=g,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
    return (a,b,c,d,e,f,g,h)

print("="*80)
print("ROTATIONSKOLLISIONEN IN K1-1 - erschoepfend")
print("="*80)
print("  Gesucht: Paare (v, rotl(v,r)) mit  F(rotl(v,r)) == rotl(F(v),r)")
print("  auf den obersten k Bits. Erschoepfend ueber alle 65.536 v.\n")

def zaehle_treffer(runden, r, k_bits, erschoepfend=True, schritt=1):
    """Wieviele v erfuellen die Rotationsrelation auf den obersten k Bits?"""
    ivr=[rotl(x,r) for x in IV]
    treffer=0; geprueft=0
    for v in range(0,65536,schritt):
        A=kompress([0]*7+[v]+PAD,runden,IV)
        B=kompress([0]*7+[rotl(v,r)]+PAD,runden,ivr)
        Ar=[rotl(z,r) for z in A]
        # oberste k Bits des ersten Registers vergleichen
        if (Ar[0]>>(32-k_bits))==(B[0]>>(32-k_bits)):
            treffer+=1
        geprueft+=1
    return treffer, geprueft

print(f"  {'Runden':>7} {'k=8 Bit':>18} {'k=16 Bit':>18} {'k=24 Bit':>18}")
print(f"  {'':7} {'gef. / erwartet':>18} {'gef. / erwartet':>18} {'gef. / erwartet':>18}")
for runden in [4,6,8,10,12,16,20]:
    zeile=f"  {runden:>7}"
    for kb in [8,16,24]:
        t,g=zaehle_treffer(runden,1,kb,schritt=1 if runden<=12 else 3)
        erw=g/(2**kb)
        zeile+=f"  {t:>7} / {erw:>8.2f}"
    print(zeile)
print()
print("  'erwartet' = Zufallserwartung. Deutlich mehr Treffer = Restsymmetrie.\n")

print("="*80)
print("VERGLEICH: dieselbe Messung bei K1 (freie Eingabe)")
print("="*80)
rng=random.Random(4)
def zaehle_k1(runden,r,k_bits,proben=20000):
    ivr=[rotl(x,r) for x in IV]
    t=0
    for _ in range(proben):
        W=[rng.randrange(1<<32) for _ in range(8)]
        A=kompress(W+PAD,runden,IV)
        B=kompress([rotl(w,r) for w in W]+PAD,runden,ivr)
        if (rotl(A[0],r)>>(32-k_bits))==(B[0]>>(32-k_bits)): t+=1
    return t,proben
print(f"  {'Runden':>7} {'K1-1 (k=16)':>16} {'K1 (k=16)':>14} {'erwartet':>11}")
for runden in [4,6,8,10,12,16]:
    a,ga=zaehle_treffer(runden,1,16,schritt=1)
    b,gb=zaehle_k1(runden,1,16)
    print(f"  {runden:>7} {a:>7}/{ga:<8} {b:>6}/{gb:<7} {ga/65536:>10.2f}")
print()
print("="*80)
print("DEUTUNG")
print("="*80)
print("  Liegt K1-1 bei hoeheren Runden deutlich ueber der Zufallserwartung")
print("  und ueber K1, traegt die Restsymmetrie. Sonst stirbt sie mit den")
print("  ersten Runden ab und ist nicht nutzbar.")
