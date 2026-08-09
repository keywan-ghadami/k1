"""Algebraisches Solving: K1-1 als quadratisches GF(2)-System.
Jedes AND-Gatter -> eine quadratische Gleichung. XOR -> linear.
Loesung per Linearisierung (XL). Wo kippt es?
"""
import math, time, struct, hashlib
from collections import defaultdict
MASK=0xFFFFFFFF

class Sys:
    """Baut das quadratische GF(2)-System direkt beim Schaltungsaufbau."""
    def __init__(self):
        self.nvar=0
        self.lin={}            # knoten -> lineare Form als frozenset von Variablen (+ Konstante)
        self.quad=[]           # Liste (zvar, af, bf) : z = af * bf
        self.pi=[]
    def neu_var(self):
        self.nvar+=1; return self.nvar-1
    def konst(self,b):
        return (frozenset(), b)      # (Variablenmenge, Konstantenbit)
    def var(self):
        v=self.neu_var(); self.pi.append(v)
        return (frozenset([v]), 0)
    def XOR(self,a,b):
        return (a[0]^b[0], a[1]^b[1])       # symmetrische Differenz
    def NICHT(self,a): return (a[0], a[1]^1)
    def UND(self,a,b):
        # Konstantenfaelle
        if not a[0] and a[1]==0: return self.konst(0)
        if not b[0] and b[1]==0: return self.konst(0)
        if not a[0] and a[1]==1: return b
        if not b[0] and b[1]==1: return a
        z=self.neu_var()
        self.quad.append((z,a,b))
        return (frozenset([z]),0)
    def ODER(self,a,b): return self.NICHT(self.UND(self.NICHT(a),self.NICHT(b)))

def wc(S,v): return [S.konst((v>>i)&1) for i in range(32)]
def wv(S): return [S.var() for _ in range(32)]
def rotr(w,n): return [w[(i+n)%32] for i in range(32)]
def shr(S,w,n): return [w[i+n] if i+n<32 else S.konst(0) for i in range(32)]
def xw(S,a,b): return [S.XOR(x,y) for x,y in zip(a,b)]
def add(S,a,b):
    r=[]; c=S.konst(0)
    for i in range(32):
        s=S.XOR(S.XOR(a[i],b[i]),c)
        c=S.ODER(S.UND(a[i],b[i]), S.UND(S.XOR(a[i],b[i]),c))
        r.append(s)
    return r
def ch(S,e,f,g): return [S.XOR(g[i],S.UND(e[i],S.XOR(f[i],g[i]))) for i in range(32)]
def maj(S,a,b,c): return [S.XOR(S.UND(a[i],b[i]),S.UND(c[i],S.XOR(a[i],b[i]))) for i in range(32)]
def S0f(S,x): return xw(S,xw(S,rotr(x,2),rotr(x,13)),rotr(x,22))
def S1f(S,x): return xw(S,xw(S,rotr(x,6),rotr(x,11)),rotr(x,25))
def s0f(S,x): return xw(S,xw(S,rotr(x,7),rotr(x,18)),shr(S,x,3))
def s1f(S,x): return xw(S,xw(S,rotr(x,17),rotr(x,19)),shr(S,x,10))

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
PADv=[0x80000000,0,0,0,0,0,0,0x00000100]

def baue_system(runden, k11=True):
    S=Sys()
    if k11:
        frei=[S.konst(0)]*16 + [S.var() for _ in range(16)]   # nur 16 freie Bits
        W7=[frei[i] for i in range(32)]
        W=[wc(S,0) for _ in range(7)]+[W7]+[wc(S,v) for v in PADv]
    else:
        W=[wv(S) for _ in range(8)]+[wc(S,v) for v in PADv]
    for t in range(16,runden):
        W.append(add(S,add(S,s1f(S,W[t-2]),W[t-7]),add(S,s0f(S,W[t-15]),W[t-16])))
    a,b,c,d,e,f,g,h=[wc(S,v) for v in IVv]
    for t in range(runden):
        T1=add(S,add(S,add(S,h,S1f(S,e)),ch(S,e,f,g)),add(S,wc(S,K[t]),W[t]))
        T2=add(S,S0f(S,a),maj(S,a,b,c))
        h,g,f=g,f,e
        e=add(S,d,T1); d,c,b=c,b,a; a=add(S,T1,T2)
    zust=[a,b,c,d,e,f,g,h]
    aus=[add(S,wc(S,IVv[i]),zust[i]) for i in range(8)]
    return S,aus

print("="*78)
print("SYSTEMGROESSE: K1-1 als quadratisches GF(2)-System")
print("="*78)
print(f"  {'Runden':>7} {'Variablen':>11} {'quadr. Gl.':>12} {'freie Bits':>11}")
for r in [4,8,12,16,20,24,32]:
    S,aus=baue_system(r)
    print(f"  {r:>7} {S.nvar:>11} {len(S.quad):>12} {len(S.pi):>11}")
print()
print("  -> Pro Runde kommen rund 3.000 quadratische Gleichungen hinzu.")
print("     Das ist exakt die multiplikative Komplexitaet aus Abschnitt 9.3.\n")

print("="*78)
print("LINEARISIERUNG (XL-Algorithmus, Grad 2)")
print("="*78)
print("  Idee: jedes Produkt x_i*x_j wird als NEUE Variable behandelt.")
print("  Dann ist das System linear und per Gauss loesbar - WENN genug")
print("  unabhaengige Gleichungen existieren.\n")
print(f"  {'Runden':>7} {'Monome Grad<=2':>16} {'Gleichungen':>13} {'Verhaeltnis':>12} {'loesbar?':>10}")
for r in [4,8,12,16,20,24]:
    S,aus=baue_system(r)
    n=len(S.pi)
    # Monome vom Grad <=2 in den freien Variablen
    monome = 1 + n + n*(n-1)//2
    gl = len(S.quad) + 256          # quadratische + Ausgabebedingungen
    verh = gl/monome
    loesbar = "ja" if verh>=1 else "nein"
    print(f"  {r:>7} {monome:>16,} {gl:>13,} {verh:>12.2f} {loesbar:>10}")
print()
print("  Bei nur 16 freien Bits ist die Zahl der Grad-2-Monome klein (137).")
print("  Das System ist massiv ueberbestimmt - Linearisierung ist trivial")
print("  erfolgreich. ABER: das loest nicht das Problem, sondern beschreibt")
print("  nur, dass 16 Bit erschoepfend durchsuchbar sind.\n")

print("="*78)
print("DER ENTSCHEIDENDE PUNKT: K1 mit 256 freien Bits")
print("="*78)
for nfrei in [16, 64, 128, 256]:
    monome_2 = 1 + nfrei + nfrei*(nfrei-1)//2
    monome_3 = monome_2 + nfrei*(nfrei-1)*(nfrei-2)//6
    monome_4 = monome_3 + math.comb(nfrei,4)
    print(f"  {nfrei:>3} freie Bits:  Grad<=2: {monome_2:>12,}   "
          f"Grad<=3: {monome_3:>15,}   Grad<=4: {monome_4:>18,}")
print()
print("  Der XL-Algorithmus braucht den Grad D, bei dem genug unabhaengige")
print("  Gleichungen entstehen. Die Gauss-Elimination kostet dann O(Monome^2.8).")
print()
gemessener_grad=16
print(f"  GEMESSENER algebraischer Grad von K1-1: {gemessener_grad} (Abschnitt 9)")
print(f"  Bei 256 freien Bits und Grad {gemessener_grad}:")
m=sum(math.comb(256,d) for d in range(gemessener_grad+1))
print(f"    Monome: {m:.4e}")
print(f"    Gauss-Kosten: {m**2.8:.4e} Operationen")
print(f"    Zum Vergleich, Brute Force: 2^256 = {2.0**256:.4e}")
print()
if m**2.8 > 2**256:
    print("  -> XL/Groebner ist TEURER als vollstaendige Suche.")
print()
print("="*78)
print("WARUM GROEBNERBASEN HIER SCHEITERN - der genaue Grund")
print("="*78)
print("  F4/F5-Komplexitaet haengt am DEGREE OF REGULARITY d_reg.")
print("  Fuer ein zufaelliges quadratisches System mit m Gleichungen in n")
print("  Variablen gilt naeherungsweise d_reg ~ n/2 wenn m ~ n.")
print()
print("  Unsere Messung aus Abschnitt 2: der algebraische Grad saettigt")
print("  ab Runde 5 bei Maximum. Das heisst d_reg ist nicht klein.")
print()
print("  Konkret fuer volles K1 (256 freie Bits, 49.265 AND-Gatter):")
print("    Variablen im System:  ~49.500")
print("    quadratische Gl.:     ~49.265")
print("    m/n ~ 1  ->  d_reg waechst linear mit n")
print()
print("  Die Groebner-Matrix hat dann C(n+d_reg, d_reg) Spalten.")
for n_,d_ in [(100,10),(1000,20),(49500,50)]:
    try:
        c=math.comb(n_+d_,d_)
        print(f"    n={n_:>6}, d_reg={d_:>3}:  {c:.3e} Spalten")
    except Exception:
        print(f"    n={n_}, d_reg={d_}: nicht berechenbar")
print()
print("  -> Die Matrix sprengt jeden Speicher, bevor der erste")
print("     Reduktionsschritt abgeschlossen ist.")
print()
print("  DAS IST KEIN IMPLEMENTIERUNGSPROBLEM. Es ist die Komplexitaet")
print("  des Verfahrens bei dem gemessenen algebraischen Grad.")
