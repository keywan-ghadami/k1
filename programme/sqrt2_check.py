"""Ist der sqrt(2)-Vorteil echt oder ein Umrechnungsartefakt?
Direkte Binaerberechnung ohne Dezimalumweg.
"""
import random, math
from decimal import Decimal, getcontext
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

# ---- Methode 1: DIREKT BINAER (kein Dezimalumweg) ----
K_SQRTP_BIN=[math.isqrt(p*(1<<64))&MASK for p in P]     # frac(sqrt(p))*2^32
# sqrt(2) direkt binaer: 64 aufeinanderfolgende 32-Bit-Bloecke der Binaerentwicklung
s2=math.isqrt(2*(1<<(64*32*2+2)))                        # sqrt(2)*2^(64*32+1)
s2_frac=s2 & ((1<<(64*32+1))-1)
K_SQ2_BIN=[(s2_frac>>(32*(63-i)))&MASK for i in range(64)]

# ---- Methode 2: ueber Dezimalstellen (wie im vorigen Lauf) ----
getcontext().prec=1500
def frac_to_K(dez, n=64):
    stellen=700
    frac=int(dez[:stellen]); nenner=10**stellen
    bits=(frac*(1<<(n*32)))//nenner
    bits&=(1<<(n*32))-1
    return [(bits>>(32*(n-1-i)))&MASK for i in range(n)]
K_SQ2_DEZ=frac_to_K(str(Decimal(2).sqrt())[2:]*2)
# Primzahl-Wurzeln ueber Dezimal
dez_all=""
for p in P:
    dez_all+=str(Decimal(p).sqrt()).split('.')[1]
K_SQRTP_DEZ=frac_to_K(dez_all)

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

def rot_test(K,runden,seed,proben=400):
    rng=random.Random(seed); tot=0;bits=0
    for r in (1,3,7,11):
        ivr=[rotl(x,r) for x in IV]
        for _ in range(proben//4):
            W=[rng.randrange(1<<32) for _ in range(16)]
            A=kompress(K,W,runden,IV)
            B=kompress(K,[rotl(w,r) for w in W],runden,ivr)
            for x,y in zip([rotl(v,r) for v in A],B):
                tot+=32-bin(x^y).count('1'); bits+=32
    return tot/bits

print("="*82)
print("SCHRITT 1: unterscheiden sich die Konstanten je nach Methode?")
print("="*82)
def stats(K,name):
    mw=sum(K)/len(K)/2**32
    bd=sum(bin(k).count('1') for k in K)/(64*32)
    # Autokorrelation aufeinanderfolgender Konstanten
    d=[abs(K[i+1]-K[i]) for i in range(63)]
    print(f"  {name:<34} Mittel {mw:.4f}  Bitdichte {bd:.4f}")
stats(K_SQRTP_BIN,"Primzahlwurzeln, BINAER")
stats(K_SQRTP_DEZ,"Primzahlwurzeln, ueber Dezimal")
stats(K_SQ2_BIN,"sqrt(2), BINAER")
stats(K_SQ2_DEZ,"sqrt(2), ueber Dezimal")
stats(K_ECHT,"echte SHA-Konstanten")
print()

print("="*82)
print("SCHRITT 2: Rotationstest, beide Methoden im Vergleich")
print("="*82)
ZUF=[]
for s in range(40):
    r=random.Random(90000+s); ZUF.append([r.randrange(1<<32) for _ in range(64)])
KAND=[("echte SHA-Konstanten",K_ECHT),
      ("Primzahlwurzeln BINAER",K_SQRTP_BIN),
      ("Primzahlwurzeln DEZIMAL",K_SQRTP_DEZ),
      ("sqrt(2) BINAER",K_SQ2_BIN),
      ("sqrt(2) DEZIMAL",K_SQ2_DEZ)]
ges={n:[] for n,_ in KAND}
for runden in [1,2,3,4]:
    seed=4000+runden*137
    zz=[rot_test(K,runden,seed) for K in ZUF]
    mu=sum(zz)/len(zz); sd=(sum((x-mu)**2 for x in zz)/len(zz))**0.5
    print(f"\n--- Runde {runden} ---  Zufall: {mu:.4%} +/- {sd:.4%}")
    for name,K in KAND:
        v=rot_test(K,runden,seed); z=(v-mu)/sd
        ges[name].append(z)
        print(f"   {name:<28} {v:>9.4%}  z={z:>+6.2f}")
print()
print("="*82)
print("ERGEBNIS")
print("="*82)
print(f"  {'Konstantensatz':<28} {'z-Werte':<30} {'Mittel':>8}")
for name,_ in KAND:
    zs=ges[name]
    print(f"  {name:<28} {' '.join(f'{z:+5.2f}' for z in zs):<30} {sum(zs)/len(zs):>+8.2f}")
print()
print("  Wenn BINAER und DEZIMAL stark abweichen, war der Effekt ein")
print("  Artefakt der Umrechnung - nicht eine Eigenschaft der Zahl.")
