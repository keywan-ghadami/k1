"""Sigma als Element von GF(2)[x]/(x^32-1).
Invertierbar? Was folgt fuer lineare Kryptanalyse?
"""
MASK=0xFFFFFFFF

# ---- Polynomarithmetik ueber GF(2) ----
def pdeg(a): return a.bit_length()-1
def pmul(a,b):
    r=0
    while b:
        if b&1: r^=a
        a<<=1; b>>=1
    return r
def pmod(a,m):
    dm=pdeg(m)
    while pdeg(a)>=dm and a:
        a ^= m << (pdeg(a)-dm)
    return a
def pdivmod(a,b):
    q=0; db=pdeg(b)
    while a and pdeg(a)>=db:
        s=pdeg(a)-db
        q ^= 1<<s
        a ^= b<<s
    return q,a
def pgcd(a,b):
    while b: a,b = b, pdivmod(a,b)[1]
    return a
def pgcdext(a,b):
    """erweiterter Euklid: gibt (g, u, v) mit u*a + v*b = g"""
    r0,r1=a,b; u0,u1=1,0; v0,v1=0,1
    while r1:
        q,r = pdivmod(r0,r1)
        r0,r1 = r1,r
        u0,u1 = u1, u0^pmul(q,u1)
        v0,v1 = v1, v0^pmul(q,v1)
    return r0,u0,v0

MOD = (1<<32)^1          # x^32 - 1 = x^32 + 1 ueber GF(2)

def bits_to_poly(v):
    return v
def poly_str(p):
    t=[f"x^{i}" if i>1 else ("x" if i==1 else "1") for i in range(pdeg(p),-1,-1) if (p>>i)&1]
    return " + ".join(t) if t else "0"

C_S0 = (1<<30)^(1<<19)^(1<<10)     # ROTR2, ROTR13, ROTR22 -> x^30 + x^19 + x^10
C_S1 = (1<<26)^(1<<21)^(1<<7)      # ROTR6, ROTR11, ROTR25

print("="*76)
print("SIGMA-POLYNOME IM RING GF(2)[x]/(x^32 - 1)")
print("="*76)
print(f"  Sigma0 <-> {poly_str(C_S0)}")
print(f"  Sigma1 <-> {poly_str(C_S1)}")
print()

print("="*76)
print("SCHRITT 1: Faktorisierung des Modulus")
print("="*76)
print("  Ueber GF(2) gilt x^32 + 1 = (x + 1)^32")
# Verifikation
p=1
for _ in range(32):
    p=pmul(p,(1<<1)^1)      # (x+1)^32
print(f"  Verifikation: (x+1)^32 == x^32+1 ?  {p==MOD}")
print()
print("  -> Der Ring ist NICHT halbeinfach. Er hat Nilpotente.")
print("     Ein Element ist genau dann invertierbar, wenn es nicht durch")
print("     (x+1) teilbar ist - also wenn es eine UNGERADE Zahl von Termen hat.\n")

print("="*76)
print("SCHRITT 2: sind die Sigma-Polynome invertierbar?")
print("="*76)
for name,C in [("Sigma0",C_S0),("Sigma1",C_S1)]:
    terme=bin(C).count('1')
    g=pgcd(C,MOD)
    print(f"  {name}: {terme} Terme, ggT mit x^32+1 = {poly_str(g)}")
    if g==1:
        _,u,_=pgcdext(C,MOD)
        u=pmod(u,MOD)
        probe=pmod(pmul(C,u),MOD)
        print(f"    INVERTIERBAR. Inverses: {u:#010x}")
        print(f"    Probe C * C^-1 mod (x^32+1) = {probe}  (muss 1 sein)")
    else:
        print(f"    NICHT invertierbar (ggT != 1)")
print()

print("="*76)
print("SCHRITT 3: Kern der Abbildung - wieviel Information geht verloren?")
print("="*76)
def zyklisch(a,c):
    p=pmul(a,c)
    return ((p & MASK) ^ (p>>32)) & MASK
for name,C in [("Sigma0",C_S0),("Sigma1",C_S1)]:
    # Kern: alle x mit Sigma(x) = 0. Basis des Kerns ueber GF(2) bestimmen.
    # Rang der 32x32-Matrix ermitteln
    zeilen=[zyklisch(1<<i, C) for i in range(32)]
    # Gauss ueber GF(2)
    basis=[]; rang=0
    tmp=list(zeilen)
    for b in range(31,-1,-1):
        piv=None
        for i,v in enumerate(tmp):
            if (v>>b)&1: piv=i; break
        if piv is None: continue
        pv=tmp.pop(piv); rang+=1
        tmp=[v^pv if (v>>b)&1 else v for v in tmp]
    kern=32-rang
    print(f"  {name}: Rang {rang}/32, Kerndimension {kern}")
    if kern==0:
        print(f"    -> BIJEKTIV. Kein Informationsverlust, eindeutig umkehrbar.")
    else:
        print(f"    -> {2**kern} Urbilder je Bild. Informationsverlust {kern} Bit.")
print()

print("="*76)
print("SCHRITT 4: dasselbe fuer die Schedule-Sigmas (mit SHIFT)")
print("="*76)
def s0f(x):
    r=lambda v,n:((v>>n)|(v<<(32-n)))&MASK
    return r(x,7)^r(x,18)^(x>>3)
def s1f(x):
    r=lambda v,n:((v>>n)|(v<<(32-n)))&MASK
    return r(x,17)^r(x,19)^(x>>10)
for name,fn in [("sigma0 (Schedule)",s0f),("sigma1 (Schedule)",s1f)]:
    zeilen=[fn(1<<i) for i in range(32)]
    tmp=list(zeilen); rang=0
    for b in range(31,-1,-1):
        piv=None
        for i,v in enumerate(tmp):
            if (v>>b)&1: piv=i; break
        if piv is None: continue
        pv=tmp.pop(piv); rang+=1
        tmp=[v^pv if (v>>b)&1 else v for v in tmp]
    print(f"  {name}: Rang {rang}/32, Kerndimension {32-rang}")
    if 32-rang>0:
        print(f"    -> nicht bijektiv, {2**(32-rang)} Urbilder je Bild")
print()

print("="*76)
print("WAS DAS FUER ANGRIFFSTECHNIKEN BEDEUTET")
print("="*76)
print("  LINEARE KRYPTANALYSE: Masken muessen rueckwaerts durch die linearen")
print("  Schichten propagiert werden. Ist Sigma bijektiv, geschieht das durch")
print("  Multiplikation mit dem Inversen - eine geschlossene Formel statt Suche.")
print()
print("  DIFFERENTIELLE KRYPTANALYSE: Fuer eine bijektive lineare Abbildung gilt")
print("  Sigma(a ^ b) = Sigma(a) ^ Sigma(b) exakt. Differenzen laufen also")
print("  DETERMINISTISCH durch Sigma - Wahrscheinlichkeit 1, kein Verlust.")
print("  Der gesamte Wahrscheinlichkeitsverlust eines differentiellen Pfades")
print("  entsteht ausschliesslich an den modularen Additionen und an Ch/Maj.")
print()
print("  Das ist der Grund, warum SHA-2-Kryptanalyse sich auf die")
print("  Uebertragsketten der Additionen konzentriert und nicht auf Sigma.")
print("  Die Ringdarstellung macht diesen bekannten Sachverhalt explizit")
print("  rechenbar, aendert aber nichts an der Schwierigkeit der Angriffe.")
