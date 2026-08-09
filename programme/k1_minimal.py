"""Pro Wertebereich: die MINIMALE Funktion OHNE Konstanten.
Operatorsatz erweitert um Mischbausteine (Sigma, xorshift, Murmur-Finalizer).
"""
import struct, hashlib, random, math, json
from collections import Counter
import numpy as np

N=65536; M32=np.uint64(0xFFFFFFFF)
def lz(b):
    n=int.from_bytes(b,'big'); return 256 if n==0 else 256-n.bit_length()

def A(v): return b'\x00'*30+struct.pack('>H',v)
def B(v): return struct.pack('>H',v)+b'\x00'*30
def C(v): return b'\x00'*15+struct.pack('>H',v)+b'\x00'*15
def D(v): return b'\xAA'*30+struct.pack('>H',v)
BEREICHE=[("A_Ende_00",A),("B_Anfang_00",B),("C_Mitte_00",C),("D_Ende_AA",D)]

Vall=np.arange(N,dtype=np.uint64)
def rotr(x,n): return ((x>>np.uint64(n))|(x<<np.uint64(32-n)))&M32
def rotl(x,n): return ((x<<np.uint64(n))|(x>>np.uint64(32-n)))&M32

# ---------- Mischbausteine ----------
UNOPS={
 'sig0':   lambda a: (rotr(a,7)^rotr(a,18)^(a>>np.uint64(3)))&M32,     # SHA-256 sigma_0
 'sig1':   lambda a: (rotr(a,17)^rotr(a,19)^(a>>np.uint64(10)))&M32,   # SHA-256 sigma_1
 'SIG0':   lambda a: (rotr(a,2)^rotr(a,13)^rotr(a,22))&M32,            # SHA-256 Sigma_0
 'SIG1':   lambda a: (rotr(a,6)^rotr(a,11)^rotr(a,25))&M32,            # SHA-256 Sigma_1
 'xorsh':  lambda a: (lambda x:(lambda y:(y^(y<<np.uint64(5)))&M32)(
                       (lambda z:(z^(z>>np.uint64(17)))&M32)(
                       (x^(x<<np.uint64(13)))&M32)))(a),               # xorshift32
 'murmur': lambda a: (lambda x:(lambda y:(y^(y>>np.uint64(16))))(
                       ((lambda z:(z^(z>>np.uint64(13)))*np.uint64(0xc2b2ae35)&M32)(
                       ((a^(a>>np.uint64(16)))*np.uint64(0x85ebca6b))&M32))))(a),
 'rotl7':  lambda a: rotl(a,7),
 'rotr11': lambda a: rotr(a,11),
 'popc':   lambda a: np.array([bin(int(x)).count('1') for x in a],dtype=np.uint64),
 'rev':    lambda a: np.array([int(format(int(x)&0xFFFFFFFF,'032b')[::-1],2) for x in a],dtype=np.uint64),
}
BINOPS=['+','-','*','^','&','|','>>','<<','%']

def ev(e,V):
    if e[0]=='v': return V.copy()
    if len(e)==2: return (UNOPS[e[0]](ev(e[1],V))&M32).astype(np.uint64)
    a=ev(e[1],V); b=ev(e[2],V); op=e[0]
    with np.errstate(all='ignore'):
        if   op=='+': r=a+b
        elif op=='-': r=a-b
        elif op=='*': r=a*b
        elif op=='^': r=a^b
        elif op=='&': r=a&b
        elif op=='|': r=a|b
        elif op=='>>': r=a>>(b&np.uint64(31))
        elif op=='<<': r=a<<(b&np.uint64(31))
        elif op=='%': r=a%np.where(b==0,np.uint64(1),b)
    return (r&M32).astype(np.uint64)

def groesse(e):
    return 1 if e[0]=='v' else 1+sum(groesse(x) for x in e[1:])
def infix(e):
    if e[0]=='v': return 'v'
    if len(e)==2: return f"{e[0]}({infix(e[1])})"
    return f"({infix(e[1])} {e[0]} {infix(e[2])})"
def ops_in(e,acc=None):
    if acc is None: acc=[]
    if e[0]=='v': return acc
    acc.append(e[0])
    for x in e[1:]: ops_in(x,acc)
    return acc

def rnd_expr(rng,t):
    if t<=0 or rng.random()<0.4: return ('v',)
    if rng.random()<0.45: return (rng.choice(list(UNOPS)), rnd_expr(rng,t-1))
    return (rng.choice(BINOPS), rnd_expr(rng,t-1), rnd_expr(rng,t-1))

def mcc(tp,fp,fn,tn):
    d=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)
    return 0.0 if d==0 else (tp*tn-fp*fn)/math.sqrt(d)

def bewerte(e,lab,ng,sparsam=0.004):
    try: out=ev(e,Vall)
    except Exception: return -9,None,None,None
    best=(-9,None,None,None)
    for Mod in (16,64,256,1024):
        r=(out%np.uint64(Mod)).astype(np.int64)
        cnt=np.bincount(r[lab],minlength=Mod)
        Cv=int(np.argmax(cnt)); pred=(r==Cv)
        tp=int((pred&lab).sum()); fp=int((pred&~lab).sum())
        s=mcc(tp,fp,ng-tp,N-ng-fp)
        if s>best[0]: best=(s,Mod,Cv,(tp,fp))
    return best[0]-sparsam*groesse(e), best[1], best[2], best[3]

results=[]
print("="*76)
print("MINIMALE KONSTANTENFREIE FUNKTION PRO WERTEBEREICH")
print("="*76)
for name,fn in BEREICHE:
    qq=np.array([lz(hashlib.sha256(fn(v)).digest()) for v in range(N)])
    g=set(int(v) for v in np.where(qq>=10)[0])
    lab=np.zeros(N,dtype=bool)
    for v in g: lab[v]=True
    ng=len(g)
    rng=random.Random(hash(name)%9999)
    pool=[rnd_expr(rng,3) for _ in range(70)]
    best=(-9,None,None,None,None)
    for it in range(30):
        sc=[]
        for e in pool:
            s,Mod,Cv,det=bewerte(e,lab,ng)
            sc.append((s,e))
            if s>best[0]: best=(s,e,Mod,Cv,det)
        sc.sort(key=lambda x:-x[0])
        elite=[e for _,e in sc[:15]]
        pool=list(elite)
        while len(pool)<70:
            if rng.random()<0.45: pool.append(rnd_expr(rng,3))
            elif rng.random()<0.5:
                pool.append((rng.choice(list(UNOPS)), rng.choice(elite)))
            else:
                pool.append((rng.choice(BINOPS), rng.choice(elite), rnd_expr(rng,2)))
    s,e,Mod,Cv,det = best
    roh,_,_,_ = bewerte(e,lab,ng,sparsam=0.0)
    tp,fp = det
    print(f"\n--- {name} ---   ({ng} gueltige Werte)")
    print(f"  FUNKTION:  ( {infix(e)} ) % {Mod} == {Cv}")
    print(f"  Groesse: {groesse(e)} Knoten, KEINE Konstanten")
    print(f"  MCC {roh:.4f}   Treffer {tp}/{ng}   Falschdurchlaesser {fp}")
    print(f"  Operatoren: {dict(Counter(ops_in(e)))}")
    results.append({"bereich":name,"funktion":f"( {infix(e)} ) % {Mod} == {Cv}",
                    "groesse":groesse(e),"mcc":roh,"treffer":tp,"gueltige":ng,
                    "falschdurchlaesser":fp,"operatoren":dict(Counter(ops_in(e)))})

with open('/mnt/user-data/outputs/k1_minimale_funktionen.json','w') as f:
    json.dump(results,f,indent=2,ensure_ascii=False)

print("\n"+"="*76)
print("STRUKTURVERGLEICH DER VIER FUNKTIONEN")
print("="*76)
for r in results:
    print(f"  {r['bereich']:<14} Groesse {r['groesse']:>2}   {r['funktion'][:60]}")
print()
mengen=[set(r['operatoren']) for r in results]
print(f"  In allen vier verwendet: {set.intersection(*mengen) or 'keine'}")
print(f"  Groessen: {[r['groesse'] for r in results]}")
print(f"  MCC:      {[round(r['mcc'],4) for r in results]}")
print("\n  Gespeichert: /mnt/user-data/outputs/k1_minimale_funktionen.json")
