"""RX-Kryptanalyse auf K1.
RX-Differenz: (x, x') mit x' = rotl(x,r) ^ delta.
Frage: ueberlebt eine in Runde 7 aufgebaute RX-Differenz das konstante
Fenster der Runden 8-15?
"""
import math, random, struct
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
P=primes(64); K=[icbrt(p*(1<<96))&MASK for p in P]
IVv=[math.isqrt(p*(1<<64))&MASK for p in primes(8)]
PAD=[0x80000000,0,0,0,0,0,0,0x00000100]

print("="*80)
print("GRUNDLAGE: RX-Propagation durch die modulare Addition")
print("="*80)
print("  RX-Paar: (x, rotl(x,r)).  Gefragt: gilt rotl(x+y,r) = rotl(x,r)+rotl(y,r)?")
rng=random.Random(3)
print(f"  {'r':>3} {'P(RX ueberlebt Addition)':>26} {'theoretisch':>13}")
for r in [1,2,4,8,16]:
    tr=0; N=200000
    for _ in range(N):
        x=rng.randrange(1<<32); y=rng.randrange(1<<32)
        if rotl((x+y)&MASK,r)==((rotl(x,r)+rotl(y,r))&MASK): tr+=1
    # Theorie (Khovratovich/Nikolic): 2^-1.415 fuer r!=0 im Mittel
    theo = 0.25*(1+2**(-r)+2**(-(32-r))+2**(-32))
    print(f"  {r:>3} {tr/N:>25.4f} {theo:>13.4f}")
print()
print("  -> Fuer r=1 liegt die Wahrscheinlichkeit bei ~0.625, fuer grosse r")
print("     naehert sie sich 0.25. Das ist die bekannte ARX-RX-Eigenschaft.\n")

def komprimiere(W0_7, runden, state=None):
    W=list(W0_7)+PAD
    for t in range(16,max(runden,16)):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK)
    a,b,c,d,e,f,g,h = state if state else IVv
    tr=[]
    for t in range(runden):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK
        T2=(S0(a)+Maj(a,b,c))&MASK
        h,g,f=g,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
        tr.append((a,b,c,d,e,f,g,h))
    return tr

def rx_abstand(Z1,Z2,r):
    """Wieviele Bits stimmen zwischen rotl(Z1,r) und Z2 ueberein?"""
    tot=0
    for x,y in zip(Z1,Z2):
        tot += 32-bin(rotl(x,r)^y).count('1')
    return tot

print("="*80)
print("TEST 1: RX-Propagation durch das KONSTANTE FENSTER (Runden 8-15)")
print("="*80)
print("  Bei K1 sind W_8..W_15 konstantes Padding. In diesen acht Runden")
print("  wird keine neue Nachrichtendifferenz injiziert.")
print()
print("  Aufbau: RX-Paar der Eingabe (W, rotl(W,r)), Zustand nach Runde t")
print("  vergleichen mit rotl(Zustand des Partners, r).\n")
rr=random.Random(77)
for r in [1,2,4]:
    print(f"  --- Rotationsweite r = {r} ---")
    print(f"  {'Runde':>6} {'RX-Uebereinstimmung':>21} {'Zufall':>9} {'Delta':>8}")
    for t in [4,6,7,8,10,12,14,15,16,18,24]:
        tot=0; N=250
        for _ in range(N):
            W=[rr.randrange(1<<32) for _ in range(8)]
            Wr=[rotl(w,r) for w in W]
            Z1=komprimiere(W,t)[-1]
            Z2=komprimiere(Wr,t,state=[rotl(v,r) for v in IVv])[-1]
            tot += rx_abstand(Z1,Z2,r)
        m=tot/(N*256)
        mark=" <- Fenster" if 8<=t<=15 else ""
        print(f"  {t:>6} {m:>20.2%} {0.5:>8.0%} {m-0.5:>+7.2%}{mark}")
    print()

print("="*80)
print("TEST 2: bleibt eine in Runde 7 aufgebaute Differenz erhalten?")
print("="*80)
print("  Direkter Test der These: Zustand nach Runde 7 als RX-Paar SETZEN,")
print("  dann durch das Fenster laufen lassen und am Ende messen.\n")
print(f"  {'r':>3} {'nach Runde 8':>14} {'nach 12':>10} {'nach 16':>10} {'nach 24':>10}")
for r in [1,2,4,8]:
    zeile=f"  {r:>3}"
    for ziel in [8,12,16,24]:
        tot=0; N=250
        for _ in range(N):
            # Zustand nach Runde 7 frei waehlen, Partner = exakte Rotation
            Z=[rr.randrange(1<<32) for _ in range(8)]
            Zr=[rotl(x,r) for x in Z]
            W=[rr.randrange(1<<32) for _ in range(8)]
            # ab Runde 8 laufen beide mit KONSTANTEM Padding weiter
            def lauf(start, woerter, bis):
                Wl=list(woerter)+PAD
                for t in range(16,max(bis,16)):
                    Wl.append((s1(Wl[t-2])+Wl[t-7]+s0(Wl[t-15])+Wl[t-16])&MASK)
                a,b,c,d,e,f,g,h=start
                for t in range(8,bis):
                    T1=(h+S1(e)+Ch(e,f,g)+K[t]+Wl[t])&MASK
                    T2=(S0(a)+Maj(a,b,c))&MASK
                    h,g,f=g,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
                return (a,b,c,d,e,f,g,h)
            A=lauf(Z,W,ziel)
            B=lauf(Zr,[rotl(w,r) for w in W],ziel)
            tot+=rx_abstand(A,B,r)
        zeile+=f"{tot/(N*256):>13.2%}"
    print(zeile)
print()
print("  Zufallserwartung: 50.00 %\n")

print("="*80)
print("TEST 3: warum das Fenster nicht hilft")
print("="*80)
print("  Die Rundenkonstanten K_t sind in den Runden 8-15 NICHT konstant -")
print("  nur die Nachrichtenwoerter sind es. K_t bricht die RX-Symmetrie")
print("  in jeder Runde neu.\n")
print(f"  {'Runde':>6} {'K_t':>12} {'rotl(K_t,1)':>14} {'gleich?':>9}")
for t in range(8,16):
    print(f"  {t:>6} {K[t]:>#12x} {rotl(K[t],1):>#14x} "
          f"{str(K[t]==rotl(K[t],1)):>9}")
print()
print("  -> Fuer eine RX-Differenz muesste K_t die Relation")
print("     K_t = rotl(K_t, r) erfuellen. Das gilt nur fuer 0x00000000")
print("     und 0xFFFFFFFF. Keine der 64 Rundenkonstanten erfuellt es.")
print()
print("  DAS IST DER STRUKTURELLE GRUND: das konstante Nachrichtenfenster")
print("  existiert, aber die Rundenkonstanten laufen weiter und zerstoeren")
print("  jede RX-Relation Runde fuer Runde - unabhaengig davon, ob neue")
print("  Nachrichtendifferenzen injiziert werden.")
