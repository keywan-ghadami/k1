"""Kreuz-Interferenz-Test: woher kommt der Symmetriebruch bei z = -2,70?
Hypothesen: (a) Eigenschaft der Quadratwurzeln, (b) Homogenitaet der
Parameterklassen, (c) Wertueberlappung IV/K.
"""
import random, math, json
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
P=primes(80)
sq  = lambda p: math.isqrt(p*(1<<64))&MASK
cb  = lambda p: icbrt(p*(1<<96))&MASK

# ---------- Die Konstantensaetze ----------
SAETZE={
 'A  FIPS (IV=sqrt, K=cbrt)':      (  [sq(p) for p in P[:8]],   [cb(p) for p in P[:64]] ),
 'B  homogen sqrt (ueberlappt)':   (  [sq(p) for p in P[:8]],   [sq(p) for p in P[:64]] ),
 'B* homogen sqrt (disjunkt)':     (  [sq(p) for p in P[:8]],   [sq(p) for p in P[8:72]] ),
 'C  homogen cbrt':                (  [cb(p) for p in P[:8]],   [cb(p) for p in P[:64]] ),
 'C* homogen cbrt (disjunkt)':     (  [cb(p) for p in P[:8]],   [cb(p) for p in P[8:72]] ),
}

print("="*84)
print("VORPRUEFUNG: Wertueberlappung zwischen IV und K")
print("="*84)
for name,(IV,K) in SAETZE.items():
    ueberlapp=len(set(IV)&set(K))
    print(f"  {name:<32} gemeinsame Werte IV/K: {ueberlapp}")
print()
print("  -> Satz B hat 8 identische Werte in IV und K_0..K_7.")
print("     Das ist eine Entartung, die Symmetrie beeinflussen kann.")
print("     Saetze mit * vermeiden sie durch disjunkte Primzahlen.\n")

def kompress(K,IV,W16,runden):
    W=list(W16)
    for t in range(16,runden):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK)
    a,b,c,d,e,f,g,h=IV
    for t in range(runden):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK
        T2=(S0(a)+Maj(a,b,c))&MASK
        h,g,f=g,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
    return (a,b,c,d,e,f,g,h)

ROTS=[1,3,5,7,9,11,13,15]        # alle zu 32 teilerfremden Weiten
PROBEN=320

def rot_matrix(K,IV,runden,seed):
    """Liefert Bit-Uebereinstimmung je Rotationsweite + Mittel."""
    werte=[]
    for r in ROTS:
        rng=random.Random(seed*100+r)
        ivr=[rotl(x,r) for x in IV]
        tot=0;bits=0
        for _ in range(PROBEN//len(ROTS)):
            W=[rng.randrange(1<<32) for _ in range(16)]
            A=kompress(K,IV,W,runden)
            B=kompress(K,ivr,[rotl(w,r) for w in W],runden)
            for x,y in zip([rotl(z,r) for z in A],B):
                tot+=32-bin(x^y).count('1'); bits+=32
        werte.append(tot/bits)
    return werte, sum(werte)/len(werte)

# ---------- Zufallsbaseline ----------
print("="*84)
print("ROHDATENMATRIX: Bit-Uebereinstimmung je Runde")
print("="*84)
ZUF=[]
for s in range(40):
    rr=random.Random(310000+s)
    ZUF.append(([sq(p) for p in P[:8]], [rr.randrange(1<<32) for _ in range(64)]))

RUNDEN=list(range(1,17))
ergebnis={n:[] for n in SAETZE}
zscores={n:[] for n in SAETZE}
print(f"  {'Runde':>6} " + " ".join(f"{n.split()[0]:>9}" for n in SAETZE) + f" {'Zufall':>10} {'Streuung':>9}")
for r in RUNDEN:
    zz=[rot_matrix(K,IV,r,seed=7)[1] for IV,K in ZUF]
    mu=sum(zz)/len(zz); sd=(sum((x-mu)**2 for x in zz)/len(zz))**0.5
    zeile=f"  {r:>6} "
    for name,(IV,K) in SAETZE.items():
        _,m=rot_matrix(K,IV,r,seed=7)
        ergebnis[name].append(m)
        z=(m-mu)/sd if sd>0 else 0
        zscores[name].append(z)
        zeile+=f"{m:>9.4%}"
    zeile+=f" {mu:>10.4%} {sd:>9.4%}"
    print(zeile)

print()
print("="*84)
print("Z-SCORE-MATRIX  (negativ = staerker gebrochen = besser)")
print("="*84)
print(f"  {'Runde':>6} " + " ".join(f"{n.split()[0]:>9}" for n in SAETZE))
for i,r in enumerate(RUNDEN):
    print(f"  {r:>6} " + " ".join(f"{zscores[n][i]:>+9.2f}" for n in SAETZE))
print(f"  {'MITTEL':>6} " + " ".join(
    f"{sum(zscores[n])/len(zscores[n]):>+9.2f}" for n in SAETZE))
print()

print("="*84)
print("ENTSCHEIDUNGSLOGIK")
print("="*84)
mA=sum(zscores['A  FIPS (IV=sqrt, K=cbrt)'])/len(RUNDEN)
mB=sum(zscores['B  homogen sqrt (ueberlappt)'])/len(RUNDEN)
mBs=sum(zscores['B* homogen sqrt (disjunkt)'])/len(RUNDEN)
mC=sum(zscores['C  homogen cbrt'])/len(RUNDEN)
mCs=sum(zscores['C* homogen cbrt (disjunkt)'])/len(RUNDEN)
print(f"  A  FIPS (gemischt)            z = {mA:+.2f}")
print(f"  B  homogen sqrt, ueberlappt   z = {mB:+.2f}")
print(f"  B* homogen sqrt, disjunkt     z = {mBs:+.2f}")
print(f"  C  homogen cbrt               z = {mC:+.2f}")
print(f"  C* homogen cbrt, disjunkt     z = {mCs:+.2f}")
print()
if mB<-2 and mBs>-1.5:
    print("  BEFUND: der Effekt verschwindet ohne die IV/K-Wertueberlappung.")
    print("  URSACHE = ENTARTUNG, nicht Eigenschaft der Quadratwurzeln.")
elif mB<-2 and mBs<-2 and mC>-1.5:
    print("  BEFUND: Quadratwurzeln brechen staerker, Kubikwurzeln nicht.")
    print("  URSACHE = algebraische Eigenschaft der Quadratwurzeln.")
elif mB<-2 and mC<-2:
    print("  BEFUND: beide homogenen Saetze brechen staerker als der gemischte.")
    print("  URSACHE = HOMOGENITAET der Parameterklassen.")
else:
    print("  BEFUND: kein Satz weicht signifikant ab. Der urspruengliche")
    print("  z = -2,70 war nicht reproduzierbar unter verdichteter Abtastung.")
print()
json.dump({'runden':RUNDEN,'werte':ergebnis,'zscores':zscores},
          open('/mnt/user-data/outputs/kreuz_interferenz.json','w'),indent=2)
print("  Rohdaten gespeichert: kreuz_interferenz.json")
