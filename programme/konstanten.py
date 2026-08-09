"""Sind die SHA-256-Konstanten schwaecher als zufaellige?
Vier Gruppen: echt, zufaellig, Fibonacci, degeneriert (Positivkontrolle).
"""
import struct, random, math, hashlib
import numpy as np
MASK=0xFFFFFFFF
def rotr(x,n): return ((x>>n)|(x<<(32-n)))&MASK
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
P64=primes(64)
K_ECHT=[icbrt(p*(1<<96))&MASK for p in P64]
IV=[__import__('math').isqrt(p*(1<<64))&MASK for p in primes(8)]

rng=random.Random(4242)
K_ZUFALL=[rng.randrange(1<<32) for _ in range(64)]
# Fibonacci-Konstanten
fib=[1,1]
while len(fib)<70: fib.append(fib[-1]+fib[-2])
K_FIB=[f&MASK for f in fib[6:70]]
# Degeneriert: Positivkontrolle - offensichtlich schwach
K_DEGEN=[0]*64

SAETZE={'echt (Wurzeln)':K_ECHT,'zufaellig':K_ZUFALL,'Fibonacci':K_FIB,'degeneriert (alle 0)':K_DEGEN}

def kompress(K, block, runden=64):
    W=list(struct.unpack('>16I',block))
    for t in range(16,runden):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK)
    a,b,c,d,e,f,g,h=IV
    tr=[]
    for t in range(runden):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK
        T2=(S0(a)+Maj(a,b,c))&MASK
        h,g,f=g,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
        tr.append((a,b,c,d,e,f,g,h))
    return tuple((x+y)&MASK for x,y in zip(IV,(a,b,c,d,e,f,g,h))), tr

def pack(s):
    v=0
    for x in s: v=(v<<32)|x
    return v
def ham(a,b): return bin(pack(a)^pack(b)).count('1')

print("="*76)
print("TEST 1: LAWINENEFFEKT pro Runde (1 Eingabebit gekippt)")
print("="*76)
print(f"  {'Runde':>6} " + " ".join(f"{n[:12]:>13}" for n in SAETZE))
rr=random.Random(7)
paare=[]
for _ in range(120):
    m=bytes(rr.randrange(256) for _ in range(64))
    bi=rr.randrange(512)
    m2=bytearray(m); m2[bi//8]^=1<<(bi%8)
    paare.append((m,bytes(m2)))
kurven={n:[] for n in SAETZE}
for t in [1,2,4,8,16,32,64]:
    zeile=f"  {t:>6} "
    for name,K in SAETZE.items():
        tot=0
        for m,m2 in paare:
            _,tr1=kompress(K,m,t); _,tr2=kompress(K,m2,t)
            tot+=ham(tr1[-1],tr2[-1])
        mw=tot/len(paare)
        kurven[name].append(mw)
        zeile+=f"{mw:>12.1f}%" if False else f"{mw/256*100:>12.1f}%"
    print(zeile)
print("\n  Ideal: 50% ab wenigen Runden. Deutliche Abweichung = Schwaeche.\n")

print("="*76)
print("TEST 2: BIT-BIAS der Ausgabe")
print("="*76)
print(f"  {'Konstantensatz':<24} {'max |Bias|':>12} {'Sigma':>10} {'Bewertung'}")
Nb=3000
for name,K in SAETZE.items():
    cnt=np.zeros(256)
    for i in range(Nb):
        m=struct.pack('>I',i)+bytes(60)
        H,_=kompress(K,m)
        v=pack(H)
        for b in range(256):
            cnt[b]+=(v>>b)&1
    bias=np.abs(cnt/Nb-0.5).max()
    sd=0.5/math.sqrt(Nb)
    bew="AUFFAELLIG" if bias>4*sd else "unauffaellig"
    print(f"  {name:<24} {bias:>12.5f} {bias/sd:>10.2f} {bew}")
print(f"\n  Rauschgrenze bei n={Nb}: {0.5/math.sqrt(Nb):.5f}\n")

print("="*76)
print("TEST 3: KOLLISIONEN bei reduzierten Runden (Geburtstagstest)")
print("="*76)
print(f"  {'Konstantensatz':<24} {'Runden 8':>11} {'Runden 16':>11} {'Runden 24':>11}")
for name,K in SAETZE.items():
    zeile=f"  {name:<24}"
    for r in [8,16,24]:
        seen={}; koll=0
        for i in range(4000):
            m=struct.pack('>I',i)+bytes(60)
            H,_=kompress(K,m,r)
            key=pack(H)>>192          # oberste 64 Bit
            if key in seen: koll+=1
            seen[key]=i
        zeile+=f"{koll:>11}"
    print(zeile)
erw=4000*3999/2/2**64
print(f"\n  Erwartete Zufallskollisionen (64 Bit, 4000 Werte): {erw:.2e}")
print("  Jede Kollision > 0 waere ein starkes Signal.\n")

print("="*76)
print("BEWERTUNG")
print("="*76)
print("  Die degenerierte Gruppe (alle Konstanten 0) ist die POSITIVKONTROLLE:")
print("  Wenn unsere Tests dort keine Schwaeche zeigen, taugen die Tests nichts.")
print("  Zeigt sie Schwaeche, echte und zufaellige Konstanten aber nicht,")
print("  dann sind die echten Konstanten nachweislich nicht schwaecher als Zufall.")
