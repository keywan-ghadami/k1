"""Rotationskryptanalyse: brechen die echten Konstanten Rotationssymmetrie?
Positivkontrolle K=0 sollte hier ANSCHLAGEN - anders als bei Lawine/Bias.
"""
import struct, random, math
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
K_ECHT=[icbrt(p*(1<<96))&MASK for p in primes(64)]
IV=[math.isqrt(p*(1<<64))&MASK for p in primes(8)]
fib=[1,1]
while len(fib)<70: fib.append(fib[-1]+fib[-2])
K_FIB=[f&MASK for f in fib[6:70]]
K_NULL=[0]*64
IV_NULL=[0]*8

def kompress(K, W16, runden, iv):
    W=list(W16)
    for t in range(16,runden):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK)
    a,b,c,d,e,f,g,h=iv
    for t in range(runden):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK
        T2=(S0(a)+Maj(a,b,c))&MASK
        h,g,f=g,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
    return (a,b,c,d,e,f,g,h)

print("="*78)
print("ROTATIONSKRYPTANALYSE")
print("="*78)
print("  Test: gilt  F(rotl(M,r)) == rotl(F(M),r) ?")
print("  Bei perfekter Rotationssymmetrie: 100% Uebereinstimmung.")
print("  Bei gebrochener Symmetrie: ~50% (Zufall).\n")

rng=random.Random(99)
def rot_test(K, iv, runden, r=1, proben=300):
    """Anteil uebereinstimmender Bits zwischen F(rot(M)) und rot(F(M))."""
    tot=0; bits=0
    for _ in range(proben):
        W=[rng.randrange(1<<32) for _ in range(16)]
        Wr=[rotl(w,r) for w in W]
        A=kompress(K,W,runden,iv)
        B=kompress(K,Wr,runden,[rotl(x,r) for x in iv])
        Ar=[rotl(x,r) for x in A]
        for x,y in zip(Ar,B):
            tot+=32-bin(x^y).count('1'); bits+=32
    return tot/bits

print(f"  {'Runden':>7} {'K echt':>12} {'K = 0':>12} {'K Fibonacci':>14}")
for runden in [1,2,4,8,16,32,64]:
    a=rot_test(K_ECHT,IV,runden)
    b=rot_test(K_NULL,IV_NULL,runden)     # auch IV=0, sonst bricht der IV die Symmetrie
    c=rot_test(K_FIB,IV,runden)
    print(f"  {runden:>7} {a:>11.2%} {b:>11.2%} {c:>13.2%}")
print()
print("  -> Spalte 'K=0' ist die POSITIVKONTROLLE. Zeigt sie deutlich mehr")
print("     als 50%, erkennt der Test Symmetrie - und die echten Konstanten")
print("     brechen sie nachweislich.\n")

print("="*78)
print("WARUM K=0 DIE SYMMETRIE ERHAELT - die Theorie dahinter")
print("="*78)
print("  rotl kommutiert EXAKT mit: XOR, AND, OR, und damit mit Ch, Maj,")
print("  sowie mit den Rotationsanteilen von Sigma.")
print("  rotl kommutiert NICHT mit: Rechtsshift (SHR) und modularer Addition.")
print()
print("  Bei modularer Addition gilt rotl(a+b) == rotl(a)+rotl(b) nur, wenn")
print("  kein Uebertrag ueber die Rotationsgrenze laeuft.")
r_probe=100000
treffer=0
for _ in range(r_probe):
    a=rng.randrange(1<<32); b=rng.randrange(1<<32)
    if rotl((a+b)&MASK,1)==((rotl(a,1)+rotl(b,1))&MASK): treffer+=1
print(f"  Gemessen fuer r=1: rotl(a+b) == rotl(a)+rotl(b) in {treffer/r_probe:.4f}")
print(f"  Theoretischer Wert fuer ARX-Rotationsanalyse: 3/8 = 0.3750 (r beliebig)")
print(f"  Fuer r=1 erwartet man 1/2 + 1/8 = 0.6250")
print()

print("="*78)
print("DIFFERENTIELLE WAHRSCHEINLICHKEIT DER ADDITION")
print("="*78)
print("  Wie oft ueberlebt eine Eingabedifferenz die modulare Addition?")
print(f"  {'Delta':>10} {'DP gemessen':>14} {'Kommentar'}")
for delta in [1, 2, 0x80000000, 0x0000FFFF]:
    gleich=0; n=50000
    for _ in range(n):
        a=rng.randrange(1<<32); b=rng.randrange(1<<32)
        links=((a^delta)+b)&MASK
        rechts=(((a+b)&MASK)^delta)
        if links==rechts: gleich+=1
    kom=""
    if delta==0x80000000: kom="hoechstes Bit - kein Uebertrag moeglich"
    elif delta==1: kom="niedrigstes Bit"
    print(f"  {delta:>#10x} {gleich/n:>14.4f}  {kom}")
print()
print("  -> Delta = 0x80000000 hat DP = 1.0: eine Differenz im hoechstwertigen")
print("     Bit ueberlebt die Addition IMMER, weil dort kein Uebertrag entsteht.")
print("     Das ist die bekannteste ARX-Eigenschaft und der Ausgangspunkt")
print("     jeder differentiellen Analyse von SHA-2.")
