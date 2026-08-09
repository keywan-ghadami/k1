"""Genetische Programmierung: finde ein Registerprogramm, das genau die
81 gueltigen K1-1-Werte akzeptiert und alle anderen ablehnt.
Operationen: echte CPU-Befehle auf Registern.
"""
import struct, hashlib, random, math
import numpy as np

N=65536
def lz(b):
    n=int.from_bytes(b,'big'); return 256 if n==0 else 256-n.bit_length()
print("Bestimme gueltige Werte ...")
q=np.array([lz(hashlib.sha256(b'\x00'*30+struct.pack('>H',v)).digest()) for v in range(N)])
SCHWELLE=10
label=(q>=SCHWELLE).astype(np.uint8)
onset=np.where(label==1)[0]
print(f"  {len(onset)} gueltige Werte\n")

# ---------- Informationstheoretische Untergrenze ----------
print("="*72)
print("VORAB: wie kurz KANN ein solches Programm ueberhaupt sein?")
print("="*72)
k=len(onset)
bits = math.lgamma(N+1)/math.log(2) - math.lgamma(k+1)/math.log(2) - math.lgamma(N-k+1)/math.log(2)
print(f"  Auswahl von {k} aus {N} Werten: log2(C({N},{k})) = {bits:.0f} Bit")
print(f"  Ein Programm, das GENAU diese Menge beschreibt, braucht mindestens")
print(f"  {bits:.0f} Bit = {bits/8:.0f} Byte Information - egal in welcher Sprache.")
print()
print(f"  Bei ~4 Byte pro Instruktion sind das mindestens ~{bits/8/4:.0f} Instruktionen,")
print("  ES SEI DENN, das Programm leitet die Werte aus Struktur her")
print("  (dann zaehlt die Struktur, nicht die Aufzaehlung).")
print("  Genau das soll der genetische Algorithmus jetzt versuchen.\n")

# ---------- Registermaschine ----------
OPS = ['ADD','SUB','XOR','AND','OR','MUL','SHL','SHR','ROTL','NOT','MOVC']
NREG=4
MASK=0xFFFFFFFF

def rand_instr(rng, L):
    op=rng.choice(OPS)
    return (op, rng.randrange(NREG), rng.randrange(NREG), rng.randrange(NREG),
            rng.randrange(256))

def run_program(prog, X):
    """X: numpy uint32 array der Eingaben. Liefert R0 nach Ausfuehrung."""
    R=[X.copy(), np.zeros_like(X), np.zeros_like(X)+1, np.zeros_like(X)]
    for (op,dst,s1,s2,imm) in prog:
        a,b = R[s1], R[s2]
        if   op=='ADD': r=(a+b)
        elif op=='SUB': r=(a-b)
        elif op=='XOR': r=(a^b)
        elif op=='AND': r=(a&b)
        elif op=='OR' : r=(a|b)
        elif op=='MUL': r=(a*b)
        elif op=='SHL': r=(a<<(imm&31))
        elif op=='SHR': r=(a>>(imm&31))
        elif op=='ROTL':
            s=imm&31
            r=((a<<s)|(a>>((32-s)&31))) if s else a
        elif op=='NOT': r=(~a)
        elif op=='MOVC': r=np.full_like(a, imm)
        R[dst]=(r & MASK).astype(np.uint32)
    return R[0]

def predict(prog, X):
    return (run_program(prog, X) & 1).astype(np.uint8)

# ---------- Fitness: Matthews-Korrelation (robust bei 81 vs 65455) ----------
Xall=np.arange(N, dtype=np.uint32)
neg_idx=np.where(label==0)[0]
rng0=random.Random(7)
sample_neg=np.array(rng0.sample(list(neg_idx), 3000), dtype=np.uint32)
Xtrain=np.concatenate([onset.astype(np.uint32), sample_neg])
ytrain=np.concatenate([np.ones(len(onset),dtype=np.uint8), np.zeros(len(sample_neg),dtype=np.uint8)])

def mcc(pred, y):
    tp=int(((pred==1)&(y==1)).sum()); tn=int(((pred==0)&(y==0)).sum())
    fp=int(((pred==1)&(y==0)).sum()); fn=int(((pred==0)&(y==1)).sum())
    d=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)
    return 0.0 if d==0 else (tp*tn-fp*fn)/math.sqrt(d)

def fitness(prog):
    return mcc(predict(prog, Xtrain), ytrain)

# ---------- Evolution ----------
print("="*72)
print("GENETISCHER ALGORITHMUS")
print("="*72)
print(f"  Register: {NREG}, Operationen: {', '.join(OPS)}")
print(f"  Programmlaenge: 12-24 Instruktionen")
print(f"  Fitness: Matthews-Korrelation (1.0 = perfekt, 0.0 = Zufall)")
print(f"  Population 300, 120 Generationen\n")

rng=random.Random(2026)
POP=300; GEN=120; PLEN=18
pop=[[rand_instr(rng,PLEN) for _ in range(rng.randrange(12,25))] for _ in range(POP)]
best_overall=(-1,None)
for gen in range(GEN):
    scored=sorted(((fitness(p),p) for p in pop), key=lambda t:-t[0])
    if scored[0][0]>best_overall[0]:
        best_overall=(scored[0][0], scored[0][1])
    if gen%20==0 or gen==GEN-1:
        print(f"  Gen {gen:>3}: beste Fitness {scored[0][0]:.4f}   "
              f"Median {scored[len(scored)//2][0]:.4f}")
    elite=[p for _,p in scored[:POP//10]]
    newpop=list(elite)
    while len(newpop)<POP:
        if rng.random()<0.6:
            p1,p2=rng.choice(elite), rng.choice(elite)
            cut1=rng.randrange(1,len(p1)); cut2=rng.randrange(1,len(p2))
            child=p1[:cut1]+p2[cut2:]
        else:
            child=list(rng.choice(elite))
        for _ in range(rng.randrange(1,4)):
            if child and rng.random()<0.7:
                child[rng.randrange(len(child))]=rand_instr(rng,PLEN)
            elif rng.random()<0.5 and len(child)<26:
                child.insert(rng.randrange(len(child)+1), rand_instr(rng,PLEN))
            elif len(child)>8:
                child.pop(rng.randrange(len(child)))
        newpop.append(child[:26])
    pop=newpop

print()
print("="*72)
print("ERGEBNIS - Verifikation auf ALLEN 65.536 Werten")
print("="*72)
bf, bp = best_overall
pred_all = predict(bp, Xall)
tp=int(((pred_all==1)&(label==1)).sum()); fn=int(((pred_all==0)&(label==1)).sum())
fp=int(((pred_all==1)&(label==0)).sum()); tn=int(((pred_all==0)&(label==0)).sum())
print(f"  Bestes Programm: {len(bp)} Instruktionen, Trainings-MCC {bf:.4f}")
print(f"  Auf allen 65.536 Werten:")
print(f"    korrekt akzeptiert (von {len(onset)}):  {tp}")
print(f"    faelschlich abgelehnt:                {fn}")
print(f"    faelschlich akzeptiert:               {fp}")
print(f"    Gesamt-MCC:                           {mcc(pred_all,label):.4f}")
print()
if tp==len(onset) and fp==0:
    print("  PERFEKTE LOESUNG GEFUNDEN.")
else:
    print("  Keine exakte Loesung. Zum Vergleich:")
    print(f"    'immer nein' haette {N-len(onset)} von {N} richtig ({(N-len(onset))/N*100:.2f} %)")
    print(f"    und MCC = 0.0000 - also genauso brauchbar wie das Gefundene.")
print()
print("  Gefundenes Programm:")
for i,(op,d,s1,s2,imm) in enumerate(bp[:12]):
    print(f"    {i:>2}: R{d} = {op}(R{s1}, R{s2}, imm={imm})")
if len(bp)>12: print(f"    ... {len(bp)-12} weitere")
