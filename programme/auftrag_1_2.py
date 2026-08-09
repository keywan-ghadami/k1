"""Arbeitsauftrag 1: AND-Zahl auf das Minimum bringen.
Arbeitsauftrag 2: beide Kollisionsstatistiken getrennt.
"""
import math, struct, hashlib, itertools
MASK=0xFFFFFFFF

# ---------- Vorpruefung: sind die AND-minimalen Formen korrekt? ----------
print("="*80)
print("VORPRUEFUNG: AND-minimale Formen, erschoepfend ueber alle 8 Belegungen")
print("="*80)
def cy_or(a,b,c):   return (a&b)|(a&c)|(b&c)
def cy_min(a,b,c):  return ((a^c)&(b^c))^c
def maj_std(a,b,c): return (a&b)^(a&c)^(b&c)
def maj_min(a,b,c): return ((a^b)&(b^c))^b
ok_cy=ok_mj=True
print(f"  {'a b c':>7} {'cy_OR':>6} {'cy_min':>7} {'Maj_std':>8} {'Maj_min':>8}")
for a,b,c in itertools.product([0,1],repeat=3):
    v1,v2=cy_or(a,b,c),cy_min(a,b,c)
    v3,v4=maj_std(a,b,c),maj_min(a,b,c)
    ok_cy &= v1==v2; ok_mj &= v3==v4
    print(f"  {a} {b} {c}   {v1:>4} {v2:>7} {v3:>8} {v4:>8}")
print(f"\n  Uebertrag identisch: {ok_cy}   Maj identisch: {ok_mj}")
print("  AND-Kosten: OR-Form 3 AND-Aequivalente, Minimalform 1 AND + 3 XOR\n")

# ---------- XAIG ----------
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
        return self._neu('xor',a&~1,b&~1)^((a&1)^(b&1))
    def ODER(self,a,b): return self.UND(a^1,b^1)^1
    def analyse(self,ausg):
        ges=set(); st=[l>>1 for l in ausg]
        while st:
            n=st.pop()
            if n in ges: continue
            ges.add(n); kn=self.k[n]
            if kn[0] in ('and','xor'): st+=[kn[1]>>1,kn[2]>>1]
        A=sum(1 for n in ges if self.k[n][0]=='and')
        X=sum(1 for n in ges if self.k[n][0]=='xor')
        # AND-TIEFE (FHE-Kostengroesse)
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

def add_OR(g,a,b):
    r=[];c=0
    for i in range(32):
        s=g.XOR(g.XOR(a[i],b[i]),c)
        c=g.ODER(g.UND(a[i],b[i]),g.UND(g.XOR(a[i],b[i]),c))
        r.append(s)
    return r
def add_MIN(g,a,b):
    """AND-minimaler Ripple-Carry: 1 AND je Bit."""
    r=[];c=0
    for i in range(32):
        ac=g.XOR(a[i],c); bc=g.XOR(b[i],c)
        r.append(g.XOR(ac,b[i]))                 # Summe = a^b^c
        c=g.XOR(g.UND(ac,bc),c)                  # Uebertrag: 1 AND
    return r
def ch(g,e,f,gg): return [g.XOR(gg[i],g.UND(e[i],g.XOR(f[i],gg[i]))) for i in range(32)]
def maj_OR(g,a,b,c): return [g.XOR(g.UND(a[i],b[i]),g.UND(c[i],g.XOR(a[i],b[i]))) for i in range(32)]
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

def baue(minimal, runden=64):
    g=XAIG()
    ADD = add_MIN if minimal else add_OR
    MAJ = maj_MIN if minimal else maj_OR
    W=[wpi(g,f"W{i}_") for i in range(8)]+[wc(v) for v in PADv]
    for t in range(16,runden):
        W.append(ADD(g,ADD(g,s1(g,W[t-2]),W[t-7]),ADD(g,s0(g,W[t-15]),W[t-16])))
    a,b,c,d,e,f,gg,h=[wc(v) for v in IVv]
    for t in range(runden):
        T1=ADD(g,ADD(g,ADD(g,h,S1(g,e)),ch(g,e,f,gg)),ADD(g,wc(K[t]),W[t]))
        T2=ADD(g,S0(g,a),MAJ(g,a,b,c))
        h,gg,f=gg,f,e
        e=ADD(g,d,T1); d,c,b=c,b,a; a=ADD(g,T1,T2)
    zust=[a,b,c,d,e,f,gg,h]
    return g,[ADD(g,wc(IVv[i]),zust[i]) for i in range(8)]

print("="*80)
print("ARBEITSAUFTRAG 1: neue AND-Zahl")
print("="*80)
print(f"  {'Variante':<34} {'AND':>9} {'XOR':>9} {'AND-Tiefe':>11}")
for nm,mi in [("OR-Form (bisher)",False),("AND-minimal",True)]:
    g,aus=baue(mi)
    A,X,D=g.analyse([b for w in aus for b in w])
    print(f"  {nm:<34} {A:>9,} {X:>9,} {D:>11}")
    if mi: A_min,D_min=A,D
    else:  A_or=A
print(f"\n  Reduktion: {A_or-A_min:,} AND ({(A_or-A_min)/A_or*100:.1f} %)")
print(f"  Zielrechnung des Arbeitsauftrags: ~22.700")
print(f"  Gemessen: {A_min:,}   Abweichung: {A_min-22700:+,}")
print()

# ---------- Bitidentitaet ----------
print("="*80)
print("VERIFIKATION gegen hashlib")
print("="*80)
def rotr32(x,n): return ((x>>n)|(x<<(32-n)))&MASK
def sha_min(msg):
    """Referenzimplementierung mit den AND-minimalen Formen."""
    pad=msg+b'\x80'+b'\x00'*((55-len(msg))%64)+struct.pack('>Q',len(msg)*8)
    H=list(IVv)
    for off in range(0,len(pad),64):
        W=list(struct.unpack('>16I',pad[off:off+64]))
        for t in range(16,64):
            W.append((rotr32(W[t-2],17)^rotr32(W[t-2],19)^(W[t-2]>>10))
                     +W[t-7]
                     +(rotr32(W[t-15],7)^rotr32(W[t-15],18)^(W[t-15]>>3))
                     +W[t-16])
            W[t]&=MASK
        a,b,c,d,e,f,g_,h=H
        for t in range(64):
            mj=((a^b)&(b^c))^b                       # AND-minimale Maj
            T1=(h+(rotr32(e,6)^rotr32(e,11)^rotr32(e,25))
                +((e&f)^((~e&MASK)&g_))+K[t]+W[t])&MASK
            T2=((rotr32(a,2)^rotr32(a,13)^rotr32(a,22))+mj)&MASK
            h,g_,f=g_,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
        H=[(x+y)&MASK for x,y in zip(H,(a,b,c,d,e,f,g_,h))]
    return b''.join(struct.pack('>I',x) for x in H)
ok=True
for t in [b'',b'abc',b'x'*55,b'y'*100]:
    ok &= sha_min(t)==hashlib.sha256(t).digest()
print(f"  AND-minimale Maj in voller SHA-256: bitidentisch zu hashlib = {ok}\n")

print("="*80)
print("ARBEITSAUFTRAG 2: beide Kollisionsstatistiken getrennt")
print("="*80)
n=65536
werte={}
for tr in [12,16,20,24,28,32,40]:
    s={}
    for v in range(n):
        d=hashlib.sha256(b'\x00'*30+struct.pack('>H',v)).digest()
        h=int.from_bytes(d,'big')>>(256-tr)
        s[h]=s.get(h,0)+1
    belegt=len(s)
    koll=n-belegt
    werte[tr]=(belegt,koll)
print(f"  {'Bits':>5} {'belegt':>8} {'Kollisionen':>12} {'Paarzahl n(n-1)/2/2^k':>23} "
      f"{'Belegungsdefizit':>18}")
for tr,(belegt,koll) in werte.items():
    paar = n*(n-1)/2/(2**tr)
    defizit = n - (2**tr)*(1-math.exp(-n/(2**tr))) if tr<32 else n*(n-1)/2/(2**tr)
    print(f"  {tr:>5} {belegt:>8,} {koll:>12,} {paar:>23,.1f} {defizit:>18,.1f}")
print()
print("  Paarzahl: erwartete Zahl kollidierender PAARE (gilt nur fuer k gross).")
print("  Belegungsdefizit: n - erwartete Zahl belegter Faecher (Besetzungsmodell).")
print("  -> Ab 24 Bit fallen beide zusammen, darunter trennen sie sich deutlich.")
