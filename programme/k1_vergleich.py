"""Dein Experiment: kleine algebraische Funktionen in VERSCHIEDENEN
Wertebereichen finden - und vergleichen, ob sie einander aehneln.
"""
import struct, hashlib, random, math
from collections import Counter
import numpy as np

N=65536
def lz(b):
    n=int.from_bytes(b,'big'); return 256 if n==0 else 256-n.bit_length()

# ---------- Verschiedene Wertebereiche definieren ----------
def bereich_A(v):   # 2 freie Byte am Ende (unser bisheriges K1-1)
    return b'\x00'*30 + struct.pack('>H', v)
def bereich_B(v):   # 2 freie Byte am Anfang
    return struct.pack('>H', v) + b'\x00'*30
def bereich_C(v):   # 2 freie Byte in der Mitte
    return b'\x00'*15 + struct.pack('>H', v) + b'\x00'*15
def bereich_D(v):   # anderer konstanter Hintergrund
    return b'\xAA'*30 + struct.pack('>H', v)

BEREICHE = [("A: Ende, 0x00", bereich_A), ("B: Anfang, 0x00", bereich_B),
            ("C: Mitte, 0x00", bereich_C), ("D: Ende, 0xAA", bereich_D)]

print("Berechne alle Bereiche ...")
gueltige={}
for name, fn in BEREICHE:
    q=np.array([lz(hashlib.sha256(fn(v)).digest()) for v in range(N)])
    g=set(int(v) for v in np.where(q>=10)[0])
    gueltige[name]=g
    print(f"  {name:<20} {len(g):>4} gueltige Werte")
print()

# ---------- Suchraum: kleine algebraische Praedikate ----------
OPS=['+','-','*','^','&','|','>>','<<','%']
def rnd_expr(rng, tiefe):
    if tiefe<=0 or rng.random()<0.35:
        return ('v',) if rng.random()<0.6 else ('c', rng.randrange(1,1<<16))
    op=rng.choice(OPS)
    return (op, rnd_expr(rng,tiefe-1), rnd_expr(rng,tiefe-1))

def ops_in(e, acc=None):
    if acc is None: acc=[]
    if e[0] in ('v','c'): return acc
    acc.append(e[0]); ops_in(e[1],acc); ops_in(e[2],acc)
    return acc

def groesse(e):
    return 1 if e[0] in ('v','c') else 1+groesse(e[1])+groesse(e[2])

def ev(e, V):
    if e[0]=='v': return V.copy()
    if e[0]=='c': return np.full_like(V, e[1])
    a=ev(e[1],V); b=ev(e[2],V); op=e[0]
    with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
        if   op=='+': r=a+b
        elif op=='-': r=a-b
        elif op=='*': r=a*b
        elif op=='^': r=a^b
        elif op=='&': r=a&b
        elif op=='|': r=a|b
        elif op=='>>': r=a>>(b & np.uint64(31))
        elif op=='<<': r=a<<(b & np.uint64(15))
        elif op=='%': r=a%np.where(b==0,np.uint64(1),b)
    return (r & np.uint64(0xFFFFFFFF)).astype(np.uint64)

Vall=np.arange(N, dtype=np.uint64)

def mcc(tp,fp,fn,tn):
    d=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)
    return 0.0 if d==0 else (tp*tn-fp*fn)/math.sqrt(d)

def suche(gueltig_set, budget=25, seed=1):
    """Sucht Praedikat (expr(v) % M == C), das die gueltigen Werte trifft."""
    rng=random.Random(seed)
    lab=np.zeros(N,dtype=bool)
    for v in gueltig_set: lab[v]=True
    ng=len(gueltig_set)
    best=(-1,None,None,None)
    pool=[rnd_expr(rng,3) for _ in range(60)]
    for it in range(budget):
        neu=[]
        for e in pool:
            try: out=ev(e,Vall)
            except Exception: continue
            for M in (16,64,256,1024):
                r=out % np.uint64(M)
                # welcher Restklassenwert trifft am meisten Gueltige?
                cnt=np.bincount(r[lab].astype(np.int64), minlength=M)
                C=int(np.argmax(cnt))
                pred=(r==np.uint64(C))
                tp=int((pred&lab).sum()); fp=int((pred&~lab).sum())
                fn=ng-tp; tn=N-ng-fp
                s=mcc(tp,fp,fn,tn)
                neu.append((s,e,M,C))
                if s>best[0]: best=(s,e,M,C)
        neu.sort(key=lambda x:-x[0])
        elite=[x[1] for x in neu[:15]]
        pool=list(elite)
        while len(pool)<60:
            pool.append(rnd_expr(rng,3) if rng.random()<0.5 else
                        (rng.choice(OPS), rng.choice(elite), rnd_expr(rng,2)))
    return best

print("="*72)
print("SUCHE in jedem Bereich - plus Zufallskontrolle pro Bereich")
print("="*72)
ergebnisse={}
rngc=random.Random(4)
print(f"  {'Bereich':<20} {'MCC echt':>10} {'MCC Zufall':>12} {'Groesse':>9} {'Operatoren'}")
for name, fn in BEREICHE:
    b=suche(gueltige[name], seed=hash(name)%1000)
    zufall=set(rngc.sample(range(N), len(gueltige[name])))
    bz=suche(zufall, seed=hash(name)%1000+7)
    ops=Counter(ops_in(b[1]))
    ergebnisse[name]=(b, ops)
    top=", ".join(f"{o}x{c}" for o,c in ops.most_common(4))
    print(f"  {name:<20} {b[0]:>10.4f} {bz[0]:>12.4f} {groesse(b[1]):>9}  {top}")

print()
print("="*72)
print("VERGLEICH - deine eigentliche Frage")
print("="*72)
print("  Aehneln sich die gefundenen Funktionen zwischen den Bereichen?\n")

print("  a) OPERATOREN:")
alle_ops=Counter()
for name,(b,ops) in ergebnisse.items():
    alle_ops.update(ops)
    print(f"     {name:<20} {dict(ops)}")
print()
# Ueberlappung der Operatormengen
mengen=[set(ops.keys()) for _,(b,ops) in ergebnisse.items()]
gemeinsam=set.intersection(*mengen) if mengen else set()
vereinigt=set.union(*mengen) if mengen else set()
print(f"     in ALLEN Bereichen verwendet: {gemeinsam if gemeinsam else 'keine'}")
print(f"     insgesamt verwendet:          {vereinigt}")
print(f"     -> Jaccard-Aehnlichkeit: {len(gemeinsam)/len(vereinigt) if vereinigt else 0:.2f}")
print()
print("  b) KOMPLEXITAET:")
gr=[groesse(b[1]) for _,(b,ops) in ergebnisse.items()]
print(f"     Ausdrucksgroessen: {gr}  (Mittel {sum(gr)/len(gr):.1f}, Spanne {max(gr)-min(gr)})")
print()
print("  c) UEBERTRAGBARKEIT - der entscheidende Test:")
print("     Funktioniert die in Bereich A gefundene Funktion auch in B, C, D?")
bA=ergebnisse["A: Ende, 0x00"][0]
eA, MA, CA = bA[1], bA[2], bA[3]
outA=ev(eA,Vall)
predA=(outA % np.uint64(MA))==np.uint64(CA)
print(f"     {'getestet auf':<20} {'MCC':>10}")
for name, fn in BEREICHE:
    lab=np.zeros(N,dtype=bool)
    for v in gueltige[name]: lab[v]=True
    ng=len(gueltige[name])
    tp=int((predA&lab).sum()); fp=int((predA&~lab).sum())
    s=mcc(tp,fp,ng-tp,N-ng-fp)
    print(f"     {name:<20} {s:>10.4f}")
print()
print("="*72)
print("INTERPRETATION")
print("="*72)
print("  Wenn die Funktion aus Bereich A auch in B, C, D funktioniert,")
print("  hat sie etwas ueber SHA-256 gelernt - nicht ueber Bereich A.")
print("  Faellt der MCC in den anderen Bereichen auf ~0, war es Anpassung")
print("  an genau die 81 Werte von A.")
print()
print("  Ebenso bei den Operatoren: ein echtes Muster wuerde dieselben")
print("  Operationen in allen Bereichen bevorzugen. Zufaellige Anpassung")
print("  waehlt in jedem Bereich andere.")
