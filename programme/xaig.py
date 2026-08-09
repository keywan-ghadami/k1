"""Auf die Spitze getrieben: XAIG mit nativen XOR, CSA-Addition,
Konstantenpropagation. Wie klein wird K1 auf Gatterebene?
"""
import math
from collections import defaultdict
MASK=0xFFFFFFFF

class XAIG:
    """AND-Inverter-Graph MIT nativen XOR-Knoten (XAIG/XMG)."""
    def __init__(self):
        self.k=[('c0',)]
        self.h={}
        self.stat=defaultdict(int)
    def pi(self,name):
        self.k.append(('pi',name)); return 2*(len(self.k)-1)
    def _neu(self,typ,a,b):
        if a>b: a,b=b,a
        key=(typ,a,b)
        if key in self.h: 
            self.stat['gehasht']+=1
            return self.h[key]
        self.k.append((typ,a,b)); lit=2*(len(self.k)-1)
        self.h[key]=lit; return lit
    def UND(self,a,b):
        if a==0 or b==0: return 0
        if a==1: return b
        if b==1: return a
        if a==b: return a
        if a==(b^1): return 0
        return self._neu('and',a,b)
    def XOR(self,a,b):
        if a==0: return b
        if b==0: return a
        if a==1: return b^1
        if b==1: return a^1
        if a==b: return 0
        if a==(b^1): return 1
        # Vorzeichen herausziehen: XOR(a',b) = XOR(a,b)'
        inv=(a&1)^(b&1)
        r=self._neu('xor',a&~1,b&~1)
        return r^inv
    def ODER(self,a,b): return self.UND(a^1,b^1)^1
    def zaehle(self,ausg):
        ges=set(); st=[l>>1 for l in ausg]
        while st:
            n=st.pop()
            if n in ges: continue
            ges.add(n)
            kn=self.k[n]
            if kn[0] in ('and','xor'): st+=[kn[1]>>1,kn[2]>>1]
        a=sum(1 for n in ges if self.k[n][0]=='and')
        x=sum(1 for n in ges if self.k[n][0]=='xor')
        return a,x

def wort_pi(g,nm): return [g.pi(f"{nm}{i}") for i in range(32)]
def wort_c(g,v): return [1 if (v>>i)&1 else 0 for i in range(32)]
def rotr(w,n): return [w[(i+n)%32] for i in range(32)]
def shr(w,n): return [w[i+n] if i+n<32 else 0 for i in range(32)]
def xw(g,a,b): return [g.XOR(x,y) for x,y in zip(a,b)]

def add_rca(g,a,b):
    r=[];c=0
    for i in range(32):
        s=g.XOR(g.XOR(a[i],b[i]),c)
        c=g.ODER(g.UND(a[i],b[i]), g.UND(g.XOR(a[i],b[i]),c))
        r.append(s)
    return r

def csa(g,a,b,c):
    """3:2-Kompressor: keine Uebertragskette."""
    s=[g.XOR(g.XOR(a[i],b[i]),c[i]) for i in range(32)]
    cy=[0]+[g.ODER(g.ODER(g.UND(a[i],b[i]),g.UND(a[i],c[i])),g.UND(b[i],c[i]))
            for i in range(31)]
    return s,cy

def add_viele(g, summanden):
    """Mehrere Summanden via CSA-Baum, eine einzige echte Addition am Schluss."""
    L=list(summanden)
    while len(L)>2:
        neu=[]
        while len(L)>=3:
            a,b,c=L.pop(),L.pop(),L.pop()
            s,cy=csa(g,a,b,c); neu+= [s,cy]
        neu+=L
        L=neu
    return add_rca(g,L[0],L[1]) if len(L)==2 else L[0]

def ch(g,e,f,gg): return [g.XOR(gg[i],g.UND(e[i],g.XOR(f[i],gg[i]))) for i in range(32)]
def maj(g,a,b,c): return [g.XOR(g.UND(a[i],b[i]),g.UND(c[i],g.XOR(a[i],b[i]))) for i in range(32)]
def S0(g,x): return xw(g,xw(g,rotr(x,2),rotr(x,13)),rotr(x,22))
def S1(g,x): return xw(g,xw(g,rotr(x,6),rotr(x,11)),rotr(x,25))
def s0(g,x): return xw(g,xw(g,rotr(x,7),rotr(x,18)),shr(x,3))
def s1(g,x): return xw(g,xw(g,rotr(x,17),rotr(x,19)),shr(x,10))

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

def baue(runden=64, csa_add=True, k11=False):
    g=XAIG()
    if k11:
        W=[wort_c(g,0) for _ in range(7)]+[wort_pi(g,"v")]+[wort_c(g,v) for v in PADv]
    else:
        W=[wort_pi(g,f"W{i}_") for i in range(8)]+[wort_c(g,v) for v in PADv]
    for t in range(16,runden):
        if csa_add:
            W.append(add_viele(g,[s1(g,W[t-2]),W[t-7],s0(g,W[t-15]),W[t-16]]))
        else:
            W.append(add_rca(g,add_rca(g,s1(g,W[t-2]),W[t-7]),
                              add_rca(g,s0(g,W[t-15]),W[t-16])))
    a,b,c,d,e,f,gg,h=[wort_c(g,v) for v in IVv]
    for t in range(runden):
        if csa_add:
            T1=add_viele(g,[h,S1(g,e),ch(g,e,f,gg),wort_c(g,K[t]),W[t]])
        else:
            T1=add_rca(g,add_rca(g,add_rca(g,h,S1(g,e)),ch(g,e,f,gg)),
                        add_rca(g,wort_c(g,K[t]),W[t]))
        T2=add_rca(g,S0(g,a),maj(g,a,b,c))
        h,gg,f=gg,f,e
        e=add_rca(g,d,T1)
        d,c,b=c,b,a
        a=add_rca(g,T1,T2)
    aus=add_rca(g,wort_c(g,IVv[7]),h)
    return g,aus

print("="*78)
print("K1 AUF GATTEREBENE - schrittweise Optimierung")
print("="*78)
print(f"  {'Variante':<40} {'AND':>9} {'XOR':>9} {'gesamt':>9}")
ergebnis={}
for name,kw in [("AIG-Basis (RCA, XOR=3 AND)",dict(csa_add=False)),
                ("XAIG (native XOR)",dict(csa_add=False)),
                ("XAIG + CSA-Additionsbaeume",dict(csa_add=True)),
                ("XAIG + CSA, nur K1-1",dict(csa_add=True,k11=True))]:
    g,aus=baue(64,**kw)
    a,x=g.zaehle(aus)
    # AIG-Basis: XOR als 3 AND zaehlen
    if name.startswith("AIG-Basis"):
        ges=a+3*x
        print(f"  {name:<40} {a+3*x:>9} {0:>9} {ges:>9}")
    else:
        ges=a+x
        print(f"  {name:<40} {a:>9} {x:>9} {ges:>9}")
    ergebnis[name]=ges

basis=ergebnis["AIG-Basis (RCA, XOR=3 AND)"]
print()
print(f"  {'Reduktion gegenueber AIG-Basis':<40}")
for name,v in ergebnis.items():
    if name==list(ergebnis)[0]: continue
    print(f"    {name:<44} {(basis-v)/basis*100:>6.1f} %")
print()
print(f"  Strukturell gehashte Knoten (Wiederverwendung): {g.stat['gehasht']:,}")
print()

print("="*78)
print("WAS MAN MIT DEM ERGEBNIS MACHEN KANN")
print("="*78)
print("  1. HARDWARE: die Gatterzahl bestimmt Flaeche und Leistungsaufnahme")
print("     eines ASIC direkt. Eine Reduktion um X % senkt beides.")
print()
print("  2. SAT-KODIERUNG: die CNF-Groesse waechst linear mit der Gatterzahl.")
print("     Ein kleinerer Graph gibt eine kleinere Formel - aber der Suchraum")
print("     bleibt exponentiell. Erwarteter Effekt auf die erreichbare")
print("     Rundenzahl bei Preimage-Angriffen: null bis eine Runde.")
print()
print("  3. FORMALE VERIFIKATION: kleinere Graphen sind besser handhabbar")
print("     fuer Aequivalenzpruefungen und Modellpruefung.")
print()
print("  4. KRYPTANALYTISCH: keine Auswirkung. Die Funktion bleibt bitidentisch,")
print("     der Suchraum unveraendert. Gatterzahl misst BERECHNUNGSKOSTEN,")
print("     nicht INVERTIERUNGSKOSTEN.")
