"""Cut-Rewriting auf K1: AIG bauen, strukturell hashen, Cuts umschreiben.
Ziel: wieviel Reduktion ist real erreichbar?
"""
import itertools, math
from collections import defaultdict

# ============ AIG-Infrastruktur ============
# Knoten: ('const0',) | ('pi', name) | ('and', lit_a, lit_b)
# Literal = 2*knoten_id + invertiert

class AIG:
    def __init__(self):
        self.knoten=[('const0',)]
        self.hash={}                 # strukturelles Hashing
        self.pi=[]
    def konst0(self): return 0
    def konst1(self): return 1
    def neu_pi(self,name):
        self.knoten.append(('pi',name)); self.pi.append(len(self.knoten)-1)
        return 2*(len(self.knoten)-1)
    def ist_konst(self,l): return l>>1==0
    def UND(self,a,b):
        # Konstanten-Regeln
        if a==0 or b==0: return 0
        if a==1: return b
        if b==1: return a
        if a==b: return a
        if a==(b^1): return 0
        if a>b: a,b=b,a
        key=(a,b)
        if key in self.hash: return self.hash[key]     # STRUKTURELLES HASHING
        self.knoten.append(('and',a,b))
        lit=2*(len(self.knoten)-1)
        self.hash[key]=lit
        return lit
    def ODER(self,a,b): return self.UND(a^1,b^1)^1
    def XOR(self,a,b): return self.ODER(self.UND(a,b^1), self.UND(a^1,b))
    def NICHT(self,a): return a^1
    def MUX(self,s,t,e): return self.ODER(self.UND(s,t), self.UND(s^1,e))
    def groesse(self): return sum(1 for k in self.knoten if k[0]=='and')
    def erreichbar(self,ausgaenge):
        """Nur die von den Ausgaengen erreichbaren AND-Knoten zaehlen."""
        gesehen=set(); stapel=[l>>1 for l in ausgaenge]
        while stapel:
            n=stapel.pop()
            if n in gesehen: continue
            gesehen.add(n)
            k=self.knoten[n]
            if k[0]=='and': stapel += [k[1]>>1, k[2]>>1]
        return sum(1 for n in gesehen if self.knoten[n][0]=='and')

# ============ SHA-256-Bausteine auf Bitebene ============
MASK=0xFFFFFFFF
def wort_pi(g,name): return [g.neu_pi(f"{name}{i}") for i in range(32)]
def wort_konst(g,v): return [g.konst1() if (v>>i)&1 else g.konst0() for i in range(32)]
def rotr(w,n): return [w[(i+n)%32] for i in range(32)]
def shr(g,w,n): return [w[i+n] if i+n<32 else g.konst0() for i in range(32)]
def xor_w(g,a,b): return [g.XOR(x,y) for x,y in zip(a,b)]

def add_w(g,a,b):
    """Ripple-Carry-Addition, 32 Bit."""
    r=[]; c=g.konst0()
    for i in range(32):
        s=g.XOR(g.XOR(a[i],b[i]),c)
        c=g.ODER(g.UND(a[i],b[i]), g.UND(g.XOR(a[i],b[i]),c))
        r.append(s)
    return r

def ch_w(g,e,f,gg,optimiert):
    if optimiert:   # g ^ (e & (f^g))  -> 3 Ops
        return [g.XOR(gg[i], g.UND(e[i], g.XOR(f[i],gg[i]))) for i in range(32)]
    return [g.XOR(g.UND(e[i],f[i]), g.UND(g.NICHT(e[i]),gg[i])) for i in range(32)]

def maj_w(g,a,b,c,optimiert):
    if optimiert:   # (a&b) ^ (c & (a^b))  -> 4 Ops
        return [g.XOR(g.UND(a[i],b[i]), g.UND(c[i], g.XOR(a[i],b[i]))) for i in range(32)]
    return [g.XOR(g.XOR(g.UND(a[i],b[i]),g.UND(a[i],c[i])),g.UND(b[i],c[i]))
            for i in range(32)]

def S0_w(g,x): return xor_w(g,xor_w(g,rotr(x,2),rotr(x,13)),rotr(x,22))
def S1_w(g,x): return xor_w(g,xor_w(g,rotr(x,6),rotr(x,11)),rotr(x,25))
def s0_w(g,x): return xor_w(g,xor_w(g,rotr(x,7),rotr(x,18)),shr(g,x,3))
def s1_w(g,x): return xor_w(g,xor_w(g,rotr(x,17),rotr(x,19)),shr(g,x,10))

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
K=[icbrt(p*(1<<96))&MASK for p in P]
IVv=[math.isqrt(p*(1<<64))&MASK for p in primes(8)]
PADv=[0x80000000,0,0,0,0,0,0,0x00000100]

def baue_k1(optimiert, runden=64, nur_h7=True):
    g=AIG()
    W=[wort_pi(g,f"W{i}_") for i in range(8)] + [wort_konst(g,v) for v in PADv]
    for t in range(16,runden):
        W.append(add_w(g, add_w(g, s1_w(g,W[t-2]), W[t-7]),
                        add_w(g, s0_w(g,W[t-15]), W[t-16])))
    a,b,c,d,e,f,h_,hh = [wort_konst(g,v) for v in IVv]
    st=[a,b,c,d,e,f,h_,hh]
    a,b,c,d,e,f,gg,h = st
    for t in range(runden):
        T1=add_w(g, add_w(g, add_w(g,h,S1_w(g,e)), ch_w(g,e,f,gg,optimiert)),
                 add_w(g, wort_konst(g,K[t]), W[t]))
        T2=add_w(g, S0_w(g,a), maj_w(g,a,b,c,optimiert))
        h,gg,f = gg,f,e
        e=add_w(g,d,T1)
        d,c,b = c,b,a
        a=add_w(g,T1,T2)
    aus = add_w(g, wort_konst(g,IVv[7]), h) if nur_h7 else None
    return g, aus

print("="*74)
print("SCHRITT 1: AIG mit strukturellem Hashing")
print("="*74)
for runden in [8,16,32,64]:
    g1,o1 = baue_k1(False, runden)
    g2,o2 = baue_k1(True,  runden)
    n1=g1.erreichbar(o1); n2=g2.erreichbar(o2)
    print(f"  {runden:>2} Runden:  Lehrbuchform {n1:>7} AND-Knoten   "
          f"mit Ch/Maj-Optimierung {n2:>7}   ({(n1-n2)/n1*100:>5.1f} % weniger)")
print()
print("  Strukturelles Hashing verschmilzt identische Teilgraphen automatisch.")
print("  Es ist bereits in der Konstruktion aktiv.\n")

# ============ Cut-Rewriting ============
print("="*74)
print("SCHRITT 2: Cut-Enumeration und Rewriting")
print("="*74)

def cuts(g, ausgaenge, k=4, max_cuts=8):
    """k-feasible Cuts pro Knoten, bottom-up."""
    ordnung=[]
    gesehen=set(); stapel=[l>>1 for l in ausgaenge]
    while stapel:
        n=stapel.pop()
        if n in gesehen: continue
        gesehen.add(n)
        kn=g.knoten[n]
        if kn[0]=='and': stapel += [kn[1]>>1, kn[2]>>1]
    ordnung=sorted(gesehen)
    C={}
    for n in ordnung:
        kn=g.knoten[n]
        if kn[0]!='and':
            C[n]=[frozenset([n])]
        else:
            ca=C.get(kn[1]>>1,[frozenset([kn[1]>>1])])
            cb=C.get(kn[2]>>1,[frozenset([kn[2]>>1])])
            menge={frozenset([n])}
            for x in ca:
                for y in cb:
                    u=x|y
                    if len(u)<=k: menge.add(u)
            C[n]=sorted(menge,key=len)[:max_cuts]
    return C,ordnung

def truth_of_cut(g,n,cut):
    """Wahrheitstabelle des Kegels ueber dem Cut (bis 4 Eingaenge)."""
    ein=sorted(cut)
    if len(ein)>4: return None
    idx={v:i for i,v in enumerate(ein)}
    memo={}
    def ev(lit):
        nd=lit>>1; inv=lit&1
        if nd in idx:
            v=[0,0]
            m=0
            for row in range(1<<len(ein)):
                if (row>>idx[nd])&1: m|=1<<row
            r=m
        elif nd==0:
            r=0
        else:
            kn=g.knoten[nd]
            if kn[0]=='pi': return None
            A=ev(kn[1]); B=ev(kn[2])
            if A is None or B is None: return None
            r=A&B
        return (~r)&((1<<(1<<len(ein)))-1) if inv else r
    return ev(2*n), ein

g,aus = baue_k1(True, 16)
basis=g.erreichbar(aus)
C,ordnung = cuts(g,aus,k=4)
anz_cuts=sum(len(v) for v in C.values())
print(f"  Beispiel 16 Runden: {basis} AND-Knoten, {anz_cuts} enumerierte 4-Cuts")

# NPN-Klassen der Cut-Funktionen zaehlen
klassen=defaultdict(int)
geprueft=0
for n in ordnung:
    if g.knoten[n][0]!='and': continue
    for cut in C[n]:
        if len(cut)<2 or len(cut)>4: continue
        r=truth_of_cut(g,n,cut)
        if r is None: continue
        tt,ein=r
        klassen[(len(ein),tt)]+=1
        geprueft+=1
        if geprueft>20000: break
    if geprueft>20000: break
print(f"  {geprueft} Cut-Funktionen ausgewertet, {len(klassen)} verschiedene")
print(f"  -> Wiederverwendungsgrad: {geprueft/max(len(klassen),1):.1f}x")
print()
print("  Ein hoher Wiederverwendungsgrad bedeutet: viele Cuts realisieren")
print("  dieselbe Funktion. Genau dort greift Rewriting - jede Klasse wird")
print("  einmal optimal implementiert und ueberall eingesetzt.")
print()
print("="*74)
print("SCHRITT 3: erreichbare Reduktion abschaetzen")
print("="*74)
# Wieviele Knoten sind Teil eines XOR-Musters? XOR kostet 3 AND im AIG,
# ist aber eine einzige Operation in XOR-AIGs (XAIG)
xor_kandidaten=0
for n in ordnung:
    kn=g.knoten[n]
    if kn[0]!='and': continue
    a,b=kn[1],kn[2]
    ka=g.knoten[a>>1]; kb=g.knoten[b>>1]
    if ka[0]=='and' and kb[0]=='and' and (a&1) and (b&1):
        # Muster (a&b)' & (a'&b')'  = XOR
        xor_kandidaten+=1
print(f"  XOR-Muster im Graphen: {xor_kandidaten} von {basis} Knoten "
      f"({xor_kandidaten/basis*100:.1f} %)")
print()
print("  SHA-256 besteht ueberwiegend aus XOR (Sigma-Funktionen, Additionen).")
print("  Im reinen AIG kostet jedes XOR 3 AND-Knoten. Ein XAIG (AIG mit")
print("  XOR-Knoten) reduziert das auf 1 - ohne jede Heuristik.")
print(f"  Geschaetzte Reduktion durch XAIG allein: bis zu "
      f"{xor_kandidaten*2/basis*100:.0f} %")
