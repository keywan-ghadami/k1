"""Verifikation der auffaellig guten Werte aus Auftrag 1 und 2."""
import math, struct, hashlib, random
MASK=0xFFFFFFFF

class XAIG:
    def __init__(self):
        self.k=[('c0',)]; self.h={}; self.pi_namen=[]
    def pi(self,n):
        self.k.append(('pi',n)); self.pi_namen.append(n); return 2*(len(self.k)-1)
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
        return self._neu('xor',a&~1,b&~1)^((a&1)^(b&1))
    def ODER(self,a,b): return self.UND(a^1,b^1)^1
    def simuliere(self, belegung, ausg):
        """Wertet den Graphen fuer eine konkrete PI-Belegung aus."""
        w={0:0}
        for i,kn in enumerate(self.k):
            if kn[0]=='c0': w[i]=0
            elif kn[0]=='pi': w[i]=belegung[kn[1]]
            elif kn[0]=='and':
                a=w[kn[1]>>1]^(kn[1]&1); b=w[kn[2]>>1]^(kn[2]&1); w[i]=a&b
            else:
                a=w[kn[1]>>1]^(kn[1]&1); b=w[kn[2]>>1]^(kn[2]&1); w[i]=a^b
        return [w[l>>1]^(l&1) for l in ausg]
    def analyse(self,ausg):
        ges=set(); st=[l>>1 for l in ausg]
        while st:
            n=st.pop()
            if n in ges: continue
            ges.add(n); kn=self.k[n]
            if kn[0] in ('and','xor'): st+=[kn[1]>>1,kn[2]>>1]
        A=sum(1 for n in ges if self.k[n][0]=='and')
        X=sum(1 for n in ges if self.k[n][0]=='xor')
        tief={}
        for n in sorted(ges):
            kn=self.k[n]
            if kn[0] in ('c0','pi'): tief[n]=0
            else:
                d=max(tief.get(kn[1]>>1,0),tief.get(kn[2]>>1,0))
                tief[n]=d+(1 if kn[0]=='and' else 0)
        return A,X,max(tief[l>>1] for l in ausg)

def wc(v): return [1 if (v>>i)&1 else 0 for i in range(32)]
def wpi(g,nm): return [g.pi(f"{nm}{i}") for i in range(32)]
def rotr(w,n): return [w[(i+n)%32] for i in range(32)]
def shr(w,n): return [w[i+n] if i+n<32 else 0 for i in range(32)]
def xw(g,a,b): return [g.XOR(x,y) for x,y in zip(a,b)]
def add_MIN(g,a,b):
    r=[];c=0; nand=0
    for i in range(32):
        ac=g.XOR(a[i],c); bc=g.XOR(b[i],c)
        r.append(g.XOR(ac,b[i]))
        c=g.XOR(g.UND(ac,bc),c)
    return r
def ch(g,e,f,gg): return [g.XOR(gg[i],g.UND(e[i],g.XOR(f[i],gg[i]))) for i in range(32)]
def maj_MIN(g,a,b,c):
    return [g.XOR(g.UND(g.XOR(a[i],b[i]),g.XOR(b[i],c[i])),b[i]) for i in range(32)]
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
P=primes(64); K=[icbrt(p*(1<<96))&MASK for p in P]
IVv=[math.isqrt(p*(1<<64))&MASK for p in primes(8)]
PADv=[0x80000000,0,0,0,0,0,0,0x00000100]

def baue(runden=64):
    g=XAIG()
    W=[wpi(g,f"W{i}_") for i in range(8)]+[wc(v) for v in PADv]
    for t in range(16,runden):
        W.append(add_MIN(g,add_MIN(g,s1(g,W[t-2]),W[t-7]),
                          add_MIN(g,s0(g,W[t-15]),W[t-16])))
    a,b,c,d,e,f,gg,h=[wc(v) for v in IVv]
    for t in range(runden):
        T1=add_MIN(g,add_MIN(g,add_MIN(g,h,S1(g,e)),ch(g,e,f,gg)),
                    add_MIN(g,wc(K[t]),W[t]))
        T2=add_MIN(g,S0(g,a),maj_MIN(g,a,b,c))
        h,gg,f=gg,f,e
        e=add_MIN(g,d,T1); d,c,b=c,b,a; a=add_MIN(g,T1,T2)
    zust=[a,b,c,d,e,f,gg,h]
    return g,[add_MIN(g,wc(IVv[i]),zust[i]) for i in range(8)]

print("="*80)
print("PRUEFUNG 1: liefert der GRAPH selbst korrekte Hashes?")
print("="*80)
print("  Der bisherige hashlib-Test prueft nur die WORTFORMEL, nicht den AIG.")
print("  Jetzt: Graph simulieren und mit hashlib vergleichen.\n")
g,aus=baue(64)
rng=random.Random(11)
ok=True
for versuch in range(5):
    msg=bytes(rng.randrange(256) for _ in range(32))
    W=list(struct.unpack('>8I',msg))
    beleg={}
    for wi in range(8):
        for bi in range(32):
            beleg[f"W{wi}_{bi}"]=(W[wi]>>bi)&1
    res=[]
    for wort in aus:
        bits=g.simuliere(beleg,wort)
        res.append(sum(b<<i for i,b in enumerate(bits)))
    graph_hash=b''.join(struct.pack('>I',x) for x in res)
    ref=hashlib.sha256(msg).digest()
    stimmt = graph_hash==ref
    ok &= stimmt
    print(f"  Versuch {versuch+1}: Graph == hashlib -> {stimmt}")
print(f"\n  GESAMT: {ok}")
if not ok:
    print("  ACHTUNG: der Graph berechnet NICHT SHA-256. Zahlen ungueltig.")
print()

A,X,D=g.analyse([b for w in aus for b in w])
print("="*80)
print("PRUEFUNG 2: analytische Nachrechnung der AND-Zahl")
print("="*80)
print(f"  Gemessen: {A:,} AND, {X:,} XOR, Tiefe {D}\n")
print("  Analytisch erwartet:")
print("    Addition AND-minimal: 1 AND je Bit, letzter Uebertrag ungenutzt = 31")
add_pro_runde=7
print(f"    Additionen je Runde: {add_pro_runde}  ->  {add_pro_runde*31} AND")
print(f"    Ch:  32 AND     Maj: 32 AND")
pro_runde=add_pro_runde*31+64
print(f"    je Runde: {pro_runde}   x64 = {pro_runde*64:,}")
sched=48*3*31
print(f"    Schedule: 48 Woerter x 3 Additionen x 31 = {sched:,}")
final=8*31
print(f"    Finaladdition: 8 x 31 = {final}")
erwartet=pro_runde*64+sched+final
print(f"    SUMME erwartet: {erwartet:,}")
print(f"    gemessen:       {A:,}")
print(f"    Differenz:      {A-erwartet:+,}  ({(A-erwartet)/erwartet*100:+.1f} %)")
print()
print("  Die Differenz erklaert sich durch Konstantenfaltung:")
print("    - ADD(K[t], W[t]) mit K konstant und W_8..W_15 konstant")
print("    - Runden 8-15: beide Operanden konstant, Addition entfaellt ganz")
print("    - strukturelles Hashing verschmilzt wiederkehrende Teilgraphen")
print()

print("="*80)
print("PRUEFUNG 3: Signifikanz der Kollisionsstatistik")
print("="*80)
n=65536
print(f"  {'Bits':>5} {'gemessen':>10} {'Belegungsdefizit':>18} {'Stdabw':>9} {'Abw. in Sigma':>14}")
for tr in [12,16,20,24,28,32]:
    s={}
    for v in range(n):
        d=hashlib.sha256(b'\x00'*30+struct.pack('>H',v)).digest()
        h=int.from_bytes(d,'big')>>(256-tr)
        s[h]=s.get(h,0)+1
    koll=n-len(s)
    m=2**tr; lam=n/m
    erw_leer=m*math.exp(-lam)
    erw_koll=n-(m-erw_leer)
    # Varianz der Zahl leerer Faecher (Poissonisierung)
    var=m*math.exp(-lam)*(1-(1+lam)*math.exp(-lam))
    sd=math.sqrt(max(var,1e-9))
    sig=(koll-erw_koll)/sd if sd>0 else 0
    print(f"  {tr:>5} {koll:>10,} {erw_koll:>18,.1f} {sd:>9.1f} {sig:>+14.2f}")
print()
print("  Bei 12 Bit ist die Uebereinstimmung TRIVIAL: 65.536 Werte auf 4.096")
print("  Faecher fuellen mit Sicherheit alle, also ist koll = n - 2^k exakt.")
print("  Der aussagekraeftige Wert ist 16 Bit - dort ist die Abweichung")
print("  ein echter statistischer Test.")
