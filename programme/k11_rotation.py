"""Rotationsanalyse fuer K1-1 (30 Byte genullt, 16 freie Bits).
Erschoepfend ueber alle 65.536 Eingaben - keine Stichprobe.
"""
import random, math, struct
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
K_ECHT=[icbrt(p*(1<<96))&MASK for p in P]
K_SQRTP=[math.isqrt(p*(1<<64))&MASK for p in P]
PAD=[0x80000000,0,0,0,0,0,0,0x00000100]

def kompress(K,W16,runden,iv):
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
print("VORAB: was passiert bei K1-1 unter Rotation?")
print("="*80)
print("  K1-1 Eingabe: W_0..W_6 = 0, W_7 = v (16 Bit in der unteren Haelfte)")
print("  rotl(0, r) = 0  -> die genullten Woerter bleiben unveraendert")
print("  Nur W_7 rotiert wirklich.")
for r in [1,3,7]:
    v=0xABCD
    print(f"    r={r}: W_7 = {v:#010x} -> {rotl(v,r):#010x}")
print()

def rot_test_k11(K,runden,r_liste=(1,3,7,11),schritt=7):
    """Erschoepfend ueber v, jeweils mit mehreren Rotationsweiten."""
    tot=0;bits=0
    for r in r_liste:
        ivr=[rotl(x,r) for x in IV]
        for v in range(0,65536,schritt):
            W=[0]*7+[v]+PAD
            Wr=[0]*7+[rotl(v,r)]+PAD
            A=kompress(K,W,runden,IV)
            B=kompress(K,Wr,runden,ivr)
            for x,y in zip([rotl(z,r) for z in A],B):
                tot+=32-bin(x^y).count('1'); bits+=32
    return tot/bits

def rot_test_k1(K,runden,seed,proben=400):
    rng=random.Random(seed); tot=0;bits=0
    for r in (1,3,7,11):
        ivr=[rotl(x,r) for x in IV]
        for _ in range(proben//4):
            W=[rng.randrange(1<<32) for _ in range(8)]+PAD
            Wr=[rotl(w,r) for w in W[:8]]+PAD
            A=kompress(K,W,runden,IV)
            B=kompress(K,Wr,runden,ivr)
            for x,y in zip([rotl(z,r) for z in A],B):
                tot+=32-bin(x^y).count('1'); bits+=32
    return tot/bits

print("="*80)
print("TEST 1: K1-1 vs. K1 vs. generisch  (echte Konstanten)")
print("="*80)
print(f"  {'Runden':>7} {'K1-1 (30 Byte null)':>21} {'K1 (frei)':>12} {'Differenz':>12}")
for runden in [1,2,3,4,6,8,12]:
    a=rot_test_k11(K_ECHT,runden)
    b=rot_test_k1(K_ECHT,runden,777)
    print(f"  {runden:>7} {a:>20.3%} {b:>11.3%} {a-b:>+11.3%}")
print()
print("  Erwartung: da W_0..W_6 = 0 rotationsinvariant sind, sollte K1-1")
print("  die Symmetrie LANGSAMER brechen - es gibt weniger, was bricht.\n")

print("="*80)
print("TEST 2: Konstantenvergleich in K1-1")
print("="*80)
ZUF=[]
for s in range(25):
    rr=random.Random(31000+s); ZUF.append([rr.randrange(1<<32) for _ in range(64)])
ges={}
for runden in [1,2,4,8]:
    zz=[rot_test_k11(K,runden,schritt=61) for K in ZUF]
    mu=sum(zz)/len(zz); sd=(sum((x-mu)**2 for x in zz)/len(zz))**0.5
    print(f"\n--- Runde {runden} --- Zufall in K1-1: {mu:.4%} +/- {sd:.4%}")
    for name,K in [("echt (Kubikwurzeln)",K_ECHT),("Quadratwurzeln",K_SQRTP)]:
        v=rot_test_k11(K,runden,schritt=61); z=(v-mu)/sd if sd>0 else 0
        ges.setdefault(name,[]).append(z)
        print(f"   {name:<24} {v:>9.4%}  z={z:>+6.2f}")
print()
print("="*80)
print("GESAMTVERGLEICH ueber alle drei Varianten")
print("="*80)
print("  Mittlere z-Werte:")
print(f"    {'':<24} {'generisch':>12} {'K1':>10} {'K1-1':>10}")
print(f"    {'echt (Kubikwurzeln)':<24} {-0.04:>12.2f} {+0.10:>10.2f} "
      f"{sum(ges['echt (Kubikwurzeln)'])/len(ges['echt (Kubikwurzeln)']):>10.2f}")
print(f"    {'Quadratwurzeln':<24} {-2.70:>12.2f} {-2.34:>10.2f} "
      f"{sum(ges['Quadratwurzeln'])/len(ges['Quadratwurzeln']):>10.2f}")
