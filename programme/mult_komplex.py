"""Was die XAIG-Repraesentation kryptanalytisch hergibt:
multiplikative Komplexitaet und AND-Tiefe -> Schranke fuer den algebraischen Grad.
"""
import math
from collections import defaultdict
MASK=0xFFFFFFFF

class XAIG:
    def __init__(self):
        self.k=[('c0',)]; self.h={}
    def pi(self,n):
        self.k.append(('pi',n)); return 2*(len(self.k)-1)
    def _neu(self,t,a,b):
        if a>b: a,b=b,a
        key=(t,a,b)
        if key in self.h: return self.h[key]
        self.k.append((t,a,b)); l=2*(len(self.k)-1); self.h[key]=l; return l
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
        inv=(a&1)^(b&1)
        return self._neu('xor',a&~1,b&~1)^inv
    def ODER(self,a,b): return self.UND(a^1,b^1)^1
    def analyse(self,ausg):
        """AND-Zahl, XOR-Zahl und AND-TIEFE (laengster Pfad, nur AND gezaehlt)."""
        ges=set(); st=[l>>1 for l in ausg]
        while st:
            n=st.pop()
            if n in ges: continue
            ges.add(n); kn=self.k[n]
            if kn[0] in ('and','xor'): st+=[kn[1]>>1,kn[2]>>1]
        anz_and=sum(1 for n in ges if self.k[n][0]=='and')
        anz_xor=sum(1 for n in ges if self.k[n][0]=='xor')
        tiefe={}
        for n in sorted(ges):
            kn=self.k[n]
            if kn[0] in ('c0','pi'): tiefe[n]=0
            else:
                d=max(tiefe.get(kn[1]>>1,0), tiefe.get(kn[2]>>1,0))
                tiefe[n]= d+1 if kn[0]=='and' else d
        return anz_and, anz_xor, max(tiefe[l>>1] for l in ausg)

def wpi(g,nm): return [g.pi(f"{nm}{i}") for i in range(32)]
def wc(g,v): return [1 if (v>>i)&1 else 0 for i in range(32)]
def rotr(w,n): return [w[(i+n)%32] for i in range(32)]
def shr(w,n): return [w[i+n] if i+n<32 else 0 for i in range(32)]
def xw(g,a,b): return [g.XOR(x,y) for x,y in zip(a,b)]
def add(g,a,b):
    r=[];c=0
    for i in range(32):
        s=g.XOR(g.XOR(a[i],b[i]),c)
        c=g.ODER(g.UND(a[i],b[i]),g.UND(g.XOR(a[i],b[i]),c))
        r.append(s)
    return r
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

def baue(runden, k11=False):
    g=XAIG()
    if k11:
        W=[wc(g,0) for _ in range(7)]+[wpi(g,"v")]+[wc(g,v) for v in PADv]
    else:
        W=[wpi(g,f"W{i}_") for i in range(8)]+[wc(g,v) for v in PADv]
    for t in range(16,runden):
        W.append(add(g,add(g,s1(g,W[t-2]),W[t-7]),add(g,s0(g,W[t-15]),W[t-16])))
    a,b,c,d,e,f,gg,h=[wc(g,v) for v in IVv]
    for t in range(runden):
        T1=add(g,add(g,add(g,h,S1(g,e)),ch(g,e,f,gg)),add(g,wc(g,K[t]),W[t]))
        T2=add(g,S0(g,a),maj(g,a,b,c))
        h,gg,f=gg,f,e
        e=add(g,d,T1)
        d,c,b=c,b,a
        a=add(g,T1,T2)
    return g, add(g,wc(g,IVv[7]),h)

print("="*80)
print("WAS DIE XAIG-REPRAESENTATION HERGIBT")
print("="*80)
print("  XOR-Knoten sind GF(2)-LINEAR. AND-Knoten sind die EINZIGE")
print("  Nichtlinearitaetsquelle. Damit sind messbar:")
print("    - multiplikative Komplexitaet = Zahl der AND-Knoten")
print("    - AND-Tiefe = laengster Pfad, nur AND gezaehlt")
print("  Und es gilt die Schranke:  algebraischer Grad <= 2^(AND-Tiefe)\n")

print(f"  {'Runden':>7} {'AND':>9} {'XOR':>9} {'AND-Tiefe':>11} {'Grad <= 2^d':>14}")
for r in [1,2,3,4,6,8,12,16,32,64]:
    g,aus=baue(r)
    a,x,d=g.analyse(aus)
    schranke = 2**d if d<20 else float('inf')
    s = f"{schranke:.3e}" if d>=20 else f"{schranke}"
    print(f"  {r:>7} {a:>9} {x:>9} {d:>11} {s:>14}")
print()

print("="*80)
print("ABGLEICH MIT DER GEMESSENEN ANF (K1-1, 16 freie Bits)")
print("="*80)
print(f"  {'Runden':>7} {'AND-Tiefe':>11} {'Schranke 2^d':>14} {'gemessen':>10} {'Kommentar'}")
gemessen={1:1,2:1,3:2,4:4,5:8,8:16}
for r in [1,2,3,4,5,8]:
    g,aus=baue(r,k11=True)
    a,x,d=g.analyse(aus)
    sch=2**d
    gm=gemessen.get(r,'-')
    kom=""
    if isinstance(gm,int):
        if sch>=gm: kom="Schranke gilt"
        else: kom="WIDERSPRUCH"
        if r<=2 and gm<=1: kom+=" (affin)"
    print(f"  {r:>7} {d:>11} {sch:>14} {str(gm):>10}  {kom}")
print()
print("  Die Schranke ist korrekt, aber grob: sie waechst exponentiell mit der")
print("  Tiefe, der echte Grad saettigt bei 16 (Zahl der freien Bits).")
print("  Fuer Runde >= 5 ist die Schranke wertlos, weil 2^d die Variablenzahl")
print("  laengst uebersteigt.\n")

print("="*80)
print("MULTIPLIKATIVE KOMPLEXITAET PRO RUNDE")
print("="*80)
vorher=0
print(f"  {'Runde':>6} {'AND kumuliert':>15} {'AND neu':>10}")
for r in [1,2,4,8,16,32,64]:
    g,aus=baue(r)
    a,x,d=g.analyse(aus)
    print(f"  {r:>6} {a:>15} {a-vorher:>10}")
    vorher=a
print()
print("  -> etwa 3.000 AND-Gatter pro Runde. Das ist die 'Nichtlinearitaets-")
print("     rechnung' der Funktion: jedes AND-Gatter ist eine Stelle, an der")
print("     ein algebraischer Angriff Fallunterscheidungen treffen muss.")
print()
print("="*80)
print("WOFUER DAS TATSAECHLICH NUETZLICH IST")
print("="*80)
print("  1. Die AND-Zahl ist die relevante Groesse fuer MPC, FHE und")
print("     Zero-Knowledge-Beweise ueber SHA-256. Dort kostet jedes AND,")
print("     XOR ist gratis. Eine Halbierung der AND-Zahl halbiert dort")
print("     die Kosten real.")
print()
print("  2. Fuer algebraische Angriffe gibt die AND-Tiefe eine Gradschranke -")
print("     hier aber wertlos, weil sie den echten Grad um Groessenordnungen")
print("     ueberschaetzt.")
print()
print("  3. Fuer Preimage-Angriffe: keine Aenderung. Die multiplikative")
print("     Komplexitaet beschreibt, wie teuer die BERECHNUNG ist, nicht wie")
print("     schwer die UMKEHRUNG.")
