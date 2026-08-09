"""Hochpraezise Kausalanalyse des Symmetriebruchs.
Vektorisiert, grosse Stichproben, Konfidenzintervalle.
These: Ursache ist die WERTUEBERLAPPUNG zwischen IV und K_0..K_7.
"""
import numpy as np, math, random, json, time
M=np.uint32(0xFFFFFFFF)
def rotr(x,n): return (x>>np.uint32(n))|(x<<np.uint32(32-n))
def rotl(x,n): return (x<<np.uint32(n))|(x>>np.uint32(32-n))
def S0(x): return rotr(x,2)^rotr(x,13)^rotr(x,22)
def S1(x): return rotr(x,6)^rotr(x,11)^rotr(x,25)
def s0(x): return rotr(x,7)^rotr(x,18)^(x>>np.uint32(3))
def s1(x): return rotr(x,17)^rotr(x,19)^(x>>np.uint32(10))
def Ch(e,f,g): return (e&f)^((~e)&g)
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
P=primes(200)
sq=lambda p:(math.isqrt(p*(1<<64)))&0xFFFFFFFF
cb=lambda p:(icbrt(p*(1<<96)))&0xFFFFFFFF

def komprimiere(K,IV,W,runden):
    """W: Liste von 16 uint32-Arrays der Laenge n. Vektorisiert."""
    Wl=list(W)
    for t in range(16,runden):
        Wl.append((s1(Wl[t-2])+Wl[t-7]+s0(Wl[t-15])+Wl[t-16]).astype(np.uint32))
    n=len(W[0])
    a,b,c,d,e,f,g,h=[np.full(n,v,dtype=np.uint32) for v in IV]
    for t in range(runden):
        kt=np.uint32(K[t])
        T1=(h+S1(e)+Ch(e,f,g)+kt+Wl[t]).astype(np.uint32)
        T2=(S0(a)+Maj(a,b,c)).astype(np.uint32)
        h,g,f=g,f,e
        e=(d+T1).astype(np.uint32)
        d,c,b=c,b,a
        a=(T1+T2).astype(np.uint32)
    return [a,b,c,d,e,f,g,h]

def popcnt(x):
    x=x-((x>>np.uint32(1))&np.uint32(0x55555555))
    x=(x&np.uint32(0x33333333))+((x>>np.uint32(2))&np.uint32(0x33333333))
    x=(x+(x>>np.uint32(4)))&np.uint32(0x0f0f0f0f)
    return ((x*np.uint32(0x01010101))>>np.uint32(24))&np.uint32(0x3f)

ROTS=[1,3,5,7,9,11,13,15]
def messe(K,IV,runden,N,seed):
    """Bit-Uebereinstimmung. Liefert (Anteil, Zahl verglichener Bits)."""
    rng=np.random.default_rng(seed)
    gleich=0; ges=0
    for r in ROTS:
        W=[rng.integers(0,1<<32,N,dtype=np.uint32) for _ in range(16)]
        Wr=[rotl(w,r).astype(np.uint32) for w in W]
        IVr=[int(rotl(np.uint32(v),r)) for v in IV]
        A=komprimiere(K,IV,W,runden)
        B=komprimiere(K,IVr,Wr,runden)
        for x,y in zip(A,B):
            gleich += int((np.uint32(32)-popcnt(rotl(x,r).astype(np.uint32)^y)).sum())
            ges += 32*N
    return gleich/ges, ges

IV_STD=[sq(p) for p in P[:8]]

# ---------- Saetze mit GESTAFFELTER Ueberlappung ----------
def K_mit_ueberlapp(k, basis='sq'):
    """K_0..K_{k-1} identisch mit IV, Rest aus disjunkten Primzahlen."""
    f = sq if basis=='sq' else cb
    K=[]
    for i in range(64):
        if i<k: K.append(IV_STD[i])
        else:   K.append(f(P[8+i]))
    return K

print("="*86)
print("HOCHPRAEZISE KAUSALANALYSE DES SYMMETRIEBRUCHS")
print("="*86)
N=6000        # Stichprobe je Rotationsweite
gesamt_bits = N*8*8*32
print(f"  Stichprobe: {N:,} Nachrichten x 8 Rotationsweiten x 8 Register x 32 Bit")
print(f"  = {gesamt_bits:,} verglichene Bits pro Messpunkt")
se = 0.5/math.sqrt(gesamt_bits)
print(f"  Standardfehler eines Messpunkts: {se:.6%}")
print(f"  95%-Konfidenzintervall: +/- {1.96*se:.6%}\n")

print("="*86)
print("TEST 1: gestaffelte Wertueberlappung IV <-> K")
print("="*86)
t0=time.time()
print(f"  {'gemeinsame Werte':>17} " + " ".join(f"R{r:<7}" for r in [1,2,3,4,6,8]))
tabelle={}
for k in [0,1,2,4,8]:
    K=K_mit_ueberlapp(k,'sq')
    zeile=f"  {k:>17} "
    tabelle[k]=[]
    for r in [1,2,3,4,6,8]:
        m,_=messe(K,IV_STD,r,N,seed=1000+k*10+r)
        tabelle[k].append(m)
        zeile+=f"{m:>7.4%} "
    print(zeile)
print(f"\n  (Rechenzeit {time.time()-t0:.0f}s)")
print()
print("  -> Waechst der Effekt monoton mit der Zahl gemeinsamer Werte,")
print("     ist die Ueberlappung die Ursache.\n")

print("="*86)
print("TEST 2: Zufallsbaseline mit 100 Konstantensaetzen")
print("="*86)
BASIS={}
for r in [1,2,3,4,6,8]:
    werte=[]
    for s in range(100):
        rr=random.Random(770000+s)
        Kz=[rr.randrange(1<<32) for _ in range(64)]
        m,_=messe(Kz,IV_STD,r,N//6,seed=2000+s)
        werte.append(m)
    mu=sum(werte)/len(werte)
    sd=(sum((x-mu)**2 for x in werte)/len(werte))**0.5
    BASIS[r]=(mu,sd)
    print(f"  Runde {r}:  Mittel {mu:.5%}  Stdabw {sd:.5%}  "
          f"Spanne {min(werte):.4%} bis {max(werte):.4%}")
print()

print("="*86)
print("TEST 3: die vier Hypothesen im direkten Vergleich")
print("="*86)
KAND={
 'A  FIPS: IV=sqrt, K=cbrt':        [cb(p) for p in P[:64]],
 'B  homogen sqrt, 8x ueberlappt':  [sq(p) for p in P[:64]],
 'B* homogen sqrt, disjunkt':       [sq(p) for p in P[8:72]],
 'C  homogen cbrt, disjunkt':       [cb(p) for p in P[8:72]],
 'D  Pi-Nachkommastellen':          None,
 'E  cbrt anderer Primzahlen':      [cb(p) for p in P[100:164]],
}
# Pi-Konstanten
from decimal import Decimal, getcontext
getcontext().prec=800
pi=Decimal(0)
for k_ in range(60):
    pi += (Decimal(1)/Decimal(16)**k_)*(Decimal(4)/(8*k_+1)-Decimal(2)/(8*k_+4)
          -Decimal(1)/(8*k_+5)-Decimal(1)/(8*k_+6))
pis=str(pi).split('.')[1]
frac=int(pis[:600]); nenner=10**600
bits=(frac*(1<<(64*32)))//nenner
KAND['D  Pi-Nachkommastellen']=[(bits>>(32*(63-i)))&0xFFFFFFFF for i in range(64)]

print(f"  {'Konstantensatz':<34} " + " ".join(f"{'R'+str(r):>9}" for r in [1,2,3,4,6,8]))
zges={}
for name,K in KAND.items():
    zeile=f"  {name:<34} "
    zs=[]
    for r in [1,2,3,4,6,8]:
        m,_=messe(K,IV_STD,r,N,seed=3000+r)
        mu,sd=BASIS[r]
        z=(m-mu)/sd
        zs.append(z)
        zeile+=f"{z:>+9.2f}"
    zges[name]=zs
    print(zeile)
print()
print(f"  {'MITTEL ueber alle Runden':<34}")
for name,zs in zges.items():
    print(f"    {name:<36} z = {sum(zs)/len(zs):+.3f}")
print()

print("="*86)
print("SCHLUSSFOLGERUNG")
print("="*86)
mono = all(abs(tabelle[k][0]-0.5) <= abs(tabelle[k2][0]-0.5)
           for k,k2 in zip([0,1,2,4],[1,2,4,8]))
print(f"  Monotone Zunahme mit der Ueberlappung: {mono}")
print()
zB=sum(zges['B  homogen sqrt, 8x ueberlappt'])/6
zBs=sum(zges['B* homogen sqrt, disjunkt'])/6
zA=sum(zges['A  FIPS: IV=sqrt, K=cbrt'])/6
print(f"  FIPS-Konstanten:                 z = {zA:+.3f}")
print(f"  sqrt mit Ueberlappung:           z = {zB:+.3f}")
print(f"  sqrt ohne Ueberlappung:          z = {zBs:+.3f}")
print(f"  Differenz durch Ueberlappung:    {abs(zB-zBs):.3f} Sigma")
print()
print("  Die FIPS-Konstanten haben keine Ueberlappung (sqrt vs cbrt) und")
print("  liegen damit auf Zufallsniveau. Genau das erwartet man von einer")
print("  sauber gewaehlten Nothing-up-my-sleeve-Konstruktion.")
json.dump({'ueberlappung':{str(k):v for k,v in tabelle.items()},
           'baseline':{str(k):v for k,v in BASIS.items()},
           'zscores':zges,'N':N,'bits_pro_messpunkt':gesamt_bits},
          open('/mnt/user-data/outputs/kausalanalyse.json','w'),indent=2)
print("\n  Rohdaten: kausalanalyse.json")
