"""GP mit optimierter Fitness. POP 2000, viele Generationen."""
import struct, hashlib, random, math, time, json
import numpy as np
M32=np.uint32(0xFFFFFFFF); N=65536
Vall=np.arange(N,dtype=np.uint32)
ZIEL=np.array([int.from_bytes(hashlib.sha256(b'\x00'*30+struct.pack('>H',v)).digest()[:4],'big')
               for v in range(N)],dtype=np.uint32)

GEW=np.array([1.0/(i+1) for i in range(32)]); GEW/=GEW.sum()
def make_lut(hi):
    lut=np.zeros(1<<16); g=GEW[0:16] if hi else GEW[16:32]
    for w in range(1<<16):
        s=0.0
        for i in range(16):
            if not (w>>(15-i))&1: s+=g[i]
        lut[w]=s
    return lut
LUT_HI=make_lut(True); LUT_LO=make_lut(False)
def nullgew(x): return LUT_HI[x>>np.uint32(16)]+LUT_LO[x&np.uint32(0xFFFF)]
def clz32(x):
    out=np.full(x.shape,32,dtype=np.int32); nz=x!=0
    out[nz]=31-np.floor(np.log2(x[nz].astype(np.float64))).astype(np.int32)
    return out

def rotr(x,n): return ((x>>np.uint32(n))|(x<<np.uint32(32-n)))
def rotl(x,n): return ((x<<np.uint32(n))|(x>>np.uint32(32-n)))
def popc(a):
    x=a.copy()
    x=x-((x>>np.uint32(1))&np.uint32(0x55555555))
    x=(x&np.uint32(0x33333333))+((x>>np.uint32(2))&np.uint32(0x33333333))
    x=(x+(x>>np.uint32(4)))&np.uint32(0x0f0f0f0f)
    return ((x*np.uint32(0x01010101))>>np.uint32(24))&np.uint32(0x3f)
UNOPS={'sig0':lambda a:rotr(a,7)^rotr(a,18)^(a>>np.uint32(3)),
 'sig1':lambda a:rotr(a,17)^rotr(a,19)^(a>>np.uint32(10)),
 'SIG0':lambda a:rotr(a,2)^rotr(a,13)^rotr(a,22),
 'SIG1':lambda a:rotr(a,6)^rotr(a,11)^rotr(a,25),
 'xorsh':lambda a:(lambda x:x^(x<<np.uint32(5)))((lambda z:z^(z>>np.uint32(17)))(a^(a<<np.uint32(13)))),
 'mur':lambda a:(lambda y:y^(y>>np.uint32(16)))((a^(a>>np.uint32(16)))*np.uint32(0x85ebca6b)),
 'rotl7':lambda a:rotl(a,7),'rotr11':lambda a:rotr(a,11),
 'popc':popc,'sq':lambda a:a*a,'not':lambda a:~a}
BINOPS=['+','-','*','^','&','|','>>','<<','%']
def ev(e,V):
    if e[0]=='v': return V
    if e[0]=='c': return np.full(N,e[1],dtype=np.uint32)
    if len(e)==2: return UNOPS[e[0]](ev(e[1],V)).astype(np.uint32)
    a=ev(e[1],V); b=ev(e[2],V); op=e[0]
    with np.errstate(all='ignore'):
        if   op=='+': r=a+b
        elif op=='-': r=a-b
        elif op=='*': r=a*b
        elif op=='^': r=a^b
        elif op=='&': r=a&b
        elif op=='|': r=a|b
        elif op=='>>': r=a>>(b&np.uint32(31))
        elif op=='<<': r=a<<(b&np.uint32(31))
        elif op=='%': r=a%np.where(b==0,np.uint32(1),b)
    return r.astype(np.uint32)
def rnd(rng,t):
    if t<=0 or rng.random()<0.3:
        return ('v',) if rng.random()<0.75 else ('c',rng.randrange(1,1<<20))
    if rng.random()<0.45: return (rng.choice(list(UNOPS)),rnd(rng,t-1))
    return (rng.choice(BINOPS),rnd(rng,t-1),rnd(rng,t-1))
def infix(e):
    if e[0]=='v': return 'v'
    if e[0]=='c': return str(e[1])
    if len(e)==2: return f"{e[0]}({infix(e[1])})"
    return f"({infix(e[1])} {e[0]} {infix(e[2])})"

perm=np.random.default_rng(42).permutation(N)
TR=perm[:N//2]; TE=perm[N//2:]

def fit(pred, ziel, idx):
    p=pred[idx]; z=ziel[idx]
    beide=p|z; falsch=p|(~z)
    s=(nullgew(beide)-nullgew(falsch)).mean()
    lauf=clz32(beide).mean()
    return s+0.3*lauf, lauf

def lauf_ga(ziel, seed, POP=2000, GEN=400, tlimit=340):
    rng=random.Random(seed)
    pool=[rnd(rng,6) for _ in range(POP)]
    best=(-9,None); kurve=[]; t0=time.time()
    for gen in range(GEN):
        sc=[]
        for e in pool:
            try: p=ev(e,Vall)
            except Exception: continue
            s,_=fit(p,ziel,TR); sc.append((s,e))
            if s>best[0]: best=(s,e)
        if not sc: break
        sc.sort(key=lambda x:-x[0])
        pb=ev(sc[0][1],Vall); st,lt=fit(pb,ziel,TE)
        kurve.append((sc[0][0],st,lt))
        elite=[e for _,e in sc[:POP//10]]
        pool=list(elite)
        while len(pool)<POP:
            r=rng.random()
            if r<0.3: pool.append(rnd(rng,6))
            elif r<0.65: pool.append((rng.choice(BINOPS),rng.choice(elite),rnd(rng,3)))
            else: pool.append((rng.choice(list(UNOPS)),rng.choice(elite)))
        if time.time()-t0>tlimit: break
    return best,kurve

s0,l0=fit(np.zeros(N,dtype=np.uint32),ZIEL,TE)
print(f"NULLLINIE (konstant 0): Fitness {s0:.6f}, Lauf {l0:.5f}\n")
print("LAUF echte Daten ..."); b,k=lauf_ga(ZIEL,2026)
ZR=ZIEL[np.random.default_rng(9).permutation(N)]
print("LAUF Zufallskontrolle ..."); bz,kz=lauf_ga(ZR,2026)
print(f"\n{'Gen':>5} {'Train':>11} {'TEST echt':>12} {'Lauf echt':>11} {'|':>2} {'TEST zuf':>11} {'Lauf zuf':>10}")
step=max(1,len(k)//10)
for gi in list(range(0,len(k),step))+[len(k)-1]:
    a=k[gi]; c=kz[gi] if gi<len(kz) else (0,0,0)
    print(f"{gi:>5} {a[0]:>11.6f} {a[1]:>12.6f} {a[2]:>11.5f} {'|':>2} {c[1]:>11.6f} {c[2]:>10.5f}")
print(f"\nGenerationen: echt {len(k)}, kontrolle {len(kz)}")
print(f"Nulllinie          : {s0:.6f}")
print(f"Bestes TEST echt   : {max(x[1] for x in k):.6f}  Lauf {max(x[2] for x in k):.5f}")
print(f"Bestes TEST zufall : {max(x[1] for x in kz):.6f}  Lauf {max(x[2] for x in kz):.5f}")
print(f"Train Anfang->Ende : {k[0][0]:.6f} -> {k[-1][0]:.6f}")
print(f"TEST  Anfang->Ende : {k[0][1]:.6f} -> {k[-1][1]:.6f}")
print(f"\nFormel: {infix(b[1])[:250]}")
json.dump({"train":[x[0] for x in k],"test":[x[1] for x in k],
           "lauf":[x[2] for x in k],"test_zufall":[x[1] for x in kz],
           "nulllinie":float(s0),"formel":infix(b[1])},
          open('/mnt/user-data/outputs/k1_gp_schnell.json','w'),indent=2)
