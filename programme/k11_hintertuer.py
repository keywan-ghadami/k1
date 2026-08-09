"""Praezise Pruefung: sind die Kubikwurzeln in K1-1 schlechter als Zufall?
Identische Abtastung fuer ALLE Kandidaten. 50 Zufallssaetze.
"""
import random, math
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
K_KUBIK=[icbrt(p*(1<<96))&MASK for p in P]      # die echten SHA-256-Konstanten
K_QUAD =[math.isqrt(p*(1<<64))&MASK for p in P]
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

# IDENTISCHE Abtastung fuer alle: feste Liste von v-Werten
VLISTE=list(range(0,65536,29))     # 2260 Werte, fuer alle Kandidaten gleich
ROTS=(1,3,5,7,11,13)

def rot_test(K,runden):
    tot=0;bits=0
    for r in ROTS:
        ivr=[rotl(x,r) for x in IV]
        for v in VLISTE:
            A=kompress(K,[0]*7+[v]+PAD,runden,IV)
            B=kompress(K,[0]*7+[rotl(v,r)]+PAD,runden,ivr)
            for x,y in zip([rotl(z,r) for z in A],B):
                tot+=32-bin(x^y).count('1'); bits+=32
    return tot/bits

print("="*80)
print("K1-1: sind die KUBIKWURZELN (echte SHA-Konstanten) schlechter als Zufall?")
print("="*80)
print(f"  Abtastung: {len(VLISTE)} v-Werte x {len(ROTS)} Rotationsweiten, identisch fuer alle")
print(f"  Zufallssaetze: 50\n")

ZUF=[]
for s in range(50):
    rr=random.Random(660000+s); ZUF.append([rr.randrange(1<<32) for _ in range(64)])

ergebnis={}
for runden in [1,2,3,4,5,6]:
    zz=[rot_test(K,runden) for K in ZUF]
    mu=sum(zz)/len(zz); sd=(sum((x-mu)**2 for x in zz)/len(zz))**0.5
    vk=rot_test(K_KUBIK,runden); zk=(vk-mu)/sd
    vq=rot_test(K_QUAD,runden);  zq=(vq-mu)/sd
    # Rang: wieviele Zufallssaetze sind BESSER (niedriger) als die Kubikwurzeln?
    rang=sum(1 for x in zz if x<vk)
    ergebnis[runden]=(zk,zq,rang)
    print(f"--- Runde {runden} ---  Zufall: {mu:.4%} +/- {sd:.4%}")
    print(f"    Kubikwurzeln (echt) {vk:>9.4%}  z={zk:>+6.2f}   Rang {rang}/50 "
          f"(so viele Zufallssaetze sind besser)")
    print(f"    Quadratwurzeln      {vq:>9.4%}  z={zq:>+6.2f}")
print()

print("="*80)
print("AUSWERTUNG DER HINTERTUER-HYPOTHESE")
print("="*80)
zk_alle=[e[0] for e in ergebnis.values()]
zq_alle=[e[1] for e in ergebnis.values()]
print(f"  Kubikwurzeln, z ueber alle Runden: {' '.join(f'{z:+.2f}' for z in zk_alle)}")
print(f"    Mittel {sum(zk_alle)/len(zk_alle):+.2f}")
print(f"  Quadratwurzeln, z:                 {' '.join(f'{z:+.2f}' for z in zq_alle)}")
print(f"    Mittel {sum(zq_alle)/len(zq_alle):+.2f}")
print()
raenge=[e[2] for e in ergebnis.values()]
print(f"  Rang der Kubikwurzeln unter 50 Zufallssaetzen: {raenge}")
print(f"  (0 = bester, 50 = schlechtester)")
print(f"  Mittlerer Rang: {sum(raenge)/len(raenge):.1f} von 50")
print()
print("  BEWERTUNG:")
mz=sum(zk_alle)/len(zk_alle)
if mz>2:
    print("  Die Kubikwurzeln sind signifikant schlechter als Zufall.")
    print("  Das waere ein ernstzunehmender Hinweis auf absichtliche Wahl.")
elif mz>1:
    print("  Die Kubikwurzeln liegen leicht ueber dem Zufallsmittel, aber")
    print("  unterhalb der Signifikanzschwelle. Bei 6 getesteten Runden und")
    print("  mehreren Kandidaten ist das nach Mehrfachtestkorrektur nicht")
    print("  von Rauschen zu unterscheiden.")
else:
    print("  Die Kubikwurzeln liegen im Zufallsbereich. Kein Hinweis auf")
    print("  absichtliche Schwaechung fuer den K1-1-Spezialfall.")
print()
print("  WICHTIG ZUR EINORDNUNG:")
print("  K1-1 ist eine Konstruktion von 2026. SHA-256 wurde 2001 veroeffentlicht.")
print("  Eine Hintertuer muesste also fuer einen Spezialfall eingebaut worden sein,")
print("  den es damals nicht gab und den niemand vorhersehen konnte.")
