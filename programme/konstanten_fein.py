"""Feinvergleich der Konstantenwahl - sauber aufgesetzt.
Korrekte IV-Rotation, unabhaengige Seeds, mehrere Rotationsweiten.
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
IV=[math.isqrt(p*(1<<64))&MASK for p in primes(8)]
K_ECHT=[icbrt(p*(1<<96))&MASK for p in primes(64)]

getcontext().prec=1500
def frac_to_K(dez_str, n=64):
    """Nachkommastellen (Dezimalstring ohne '0.') -> n echte 32-Bit-Woerter."""
    stellen=700
    frac=int(dez_str[:stellen]); nenner=10**stellen
    bits=(frac*(1<<(n*32)))//nenner
    bits &= (1<<(n*32))-1
    return [(bits>>(32*(n-1-i)))&MASK for i in range(n)]

def machin_pi(prec):
    getcontext().prec=prec+20
    def arccot(x,unity):
        s=unity//x; t=s; nn=1; xp=x*x
        while t:
            t//=xp; s+= t//(2*nn+1) if nn%2==0 else -(t//(2*nn+1)); nn+=1
        return s
    return 4*(4*arccot(5,10**(prec+20))-arccot(239,10**(prec+20)))

K_PI  = frac_to_K(str(machin_pi(900))[1:])
K_E   = frac_to_K(str(Decimal(1).exp())[2:]*2)
K_SQ2 = frac_to_K(str(Decimal(2).sqrt())[2:]*2)
K_SQ3 = frac_to_K(str(Decimal(3).sqrt())[2:]*2)
K_PHI = frac_to_K(str((Decimal(5).sqrt()-1)/2)[2:]*2)
# Quadratwurzeln der Primzahlen (statt Kubikwurzeln) als weitere Variante
K_SQRTP = [math.isqrt(p*(1<<64))&MASK for p in primes(64)]

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
    """Ueber mehrere Rotationsweiten gemittelt, IV korrekt mitrotiert."""
    rng=random.Random(seed); tot=0; bits=0
    for r in (1,3,7,11):
        ivr=[rotl(x,r) for x in IV]
        for _ in range(proben//4):
            W=[rng.randrange(1<<32) for _ in range(16)]
            A=kompress(K,W,runden,IV)
            B=kompress(K,[rotl(w,r) for w in W],runden,ivr)
            for x,y in zip([rotl(v,r) for v in A],B):
                tot+=32-bin(x^y).count('1'); bits+=32
    return tot/bits

ZUF=[]
for s in range(40):
    r=random.Random(90000+s); ZUF.append([r.randrange(1<<32) for _ in range(64)])

KANDIDATEN=[("echt: Kubikwurzeln Primzahlen",K_ECHT),
            ("Quadratwurzeln Primzahlen",K_SQRTP),
            ("Pi",K_PI),("e",K_E),("sqrt(2)",K_SQ2),
            ("sqrt(3)",K_SQ3),("goldener Schnitt",K_PHI)]

print("="*82)
print("FEINVERGLEICH DER KONSTANTENWAHL  (Rotationssymmetrie)")
print("="*82)
print("  Niedriger = Symmetrie staerker gebrochen = besser")
print("  z < -2: signifikant BESSER als Zufall   z > +2: signifikant SCHLECHTER\n")

gesamt={n:[] for n,_ in KANDIDATEN}
for runden in [1,2,3,4]:
    seed=4000+runden*137                     # unabhaengiger Seed pro Runde
    zz=[rot_test(K,runden,seed) for K in ZUF]
    mu=sum(zz)/len(zz); sd=(sum((x-mu)**2 for x in zz)/len(zz))**0.5
    print(f"--- Runde {runden} ---  Zufall (n=40): {mu:.4%} +/- {sd:.4%}")
    for name,K in KANDIDATEN:
        v=rot_test(K,runden,seed); z=(v-mu)/sd
        gesamt[name].append(z)
        mark="  BESSER" if z<-2 else ("  SCHLECHTER" if z>2 else "")
        print(f"   {name:<32} {v:>9.4%}  z={z:>+6.2f}{mark}")
    print()

print("="*82)
print("GESAMTBILD ueber alle vier Runden")
print("="*82)
print(f"  {'Konstantensatz':<32} {'z-Werte':<32} {'Mittel':>8}")
for name,_ in KANDIDATEN:
    zs=gesamt[name]
    s=" ".join(f"{z:+5.2f}" for z in zs)
    print(f"  {name:<32} {s:<32} {sum(zs)/len(zs):>+8.2f}")
print()
print("  Ein systematischer Effekt muesste in allen vier Runden dasselbe")
print("  Vorzeichen haben und im Mittel deutlich von 0 abweichen.")
print("  Bei 40 Zufallssaetzen ist der Standardfehler des Mittels ~0.16 Sigma.")
