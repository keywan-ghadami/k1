"""Kuerzester ARITHMETISCHER Ausdruck fuer die 81 gueltigen Paare.
Don't-Cares ueberall sonst. Kontrollgruppe: 81 zufaellige Paare.
"""
import struct, hashlib, random, math
import numpy as np

N=65536
def h_of(v):
    return hashlib.sha256(b'\x00'*30+struct.pack('>H',v)).digest()
def lz(b):
    n=int.from_bytes(b,'big'); return 256 if n==0 else 256-n.bit_length()

print("Berechne ...")
qual=np.array([lz(h_of(v)) for v in range(N)])
gueltig=sorted(int(v) for v in np.where(qual>=10)[0])
# Zielwert: oberste 32 Bit des Hashes
ziel={v: int.from_bytes(h_of(v)[:4],'big') for v in gueltig}
print(f"  {len(gueltig)} gueltige Paare (v -> obere 32 Bit des Hashes)\n")
print("  Beispiele:")
for v in gueltig[:5]:
    print(f"    v={v:>5}  ->  {ziel[v]:#010x}")
print()

print("="*72)
print("MASSSTAB: was ist die triviale Loesung?")
print("="*72)
print(f"  Lagrange-Interpolation durch {len(gueltig)} Punkte: Polynom Grad {len(gueltig)-1}")
print(f"  -> {len(gueltig)} Koeffizienten a {32} Bit = {len(gueltig)*32} Bit = {len(gueltig)*32//8} Byte")
print(f"  Die reine Tabelle: {len(gueltig)} Paare a (16+32) Bit = {len(gueltig)*48//8} Byte")
print("  -> Interpolation ist NICHT kuerzer als die Tabelle. Beides ist trivial.")
print(f"  Ein Ausdruck ist erst interessant, wenn er deutlich unter {len(gueltig)} Termen bleibt.\n")

# ---------- Ausdrucksbaeume ----------
BINOPS = ['+','-','*','^','&','|','>>','<<','%']
def rnd_expr(rng, tiefe):
    if tiefe<=0 or rng.random()<0.3:
        r=rng.random()
        if r<0.5: return ('v',)
        elif r<0.8: return ('c', rng.randrange(1, 1<<16))
        else: return ('c', rng.randrange(1, 1<<32))
    op=rng.choice(BINOPS)
    return (op, rnd_expr(rng,tiefe-1), rnd_expr(rng,tiefe-1))

def groesse(e):
    if e[0] in ('v','c'): return 1
    return 1+groesse(e[1])+groesse(e[2])

def evaluate(e, V):
    if e[0]=='v': return V.copy()
    if e[0]=='c': return np.full_like(V, e[1] & 0xFFFFFFFF)
    a=evaluate(e[1],V); b=evaluate(e[2],V)
    op=e[0]
    with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
        if   op=='+': r=a+b
        elif op=='-': r=a-b
        elif op=='*': r=a*b
        elif op=='^': r=a^b
        elif op=='&': r=a&b
        elif op=='|': r=a|b
        elif op=='>>': r=a>>(b & np.uint64(31))
        elif op=='<<': r=a<<(b & np.uint64(31))
        elif op=='%':
            bb=np.where(b==0, np.uint64(1), b); r=a%bb
    return (r & np.uint64(0xFFFFFFFF)).astype(np.uint64)

def treffer(e, Vs, Ts):
    try:
        out=evaluate(e, Vs)
    except Exception:
        return 0
    return int((out==Ts).sum())

def suche(paare, budget=400000, maxtiefe=4, seed=1):
    rng=random.Random(seed)
    Vs=np.array([v for v,_ in paare], dtype=np.uint64)
    Ts=np.array([t for _,t in paare], dtype=np.uint64)
    best=(0,None)
    # Zufallssuche + lokale Mutation
    pool=[rnd_expr(rng,maxtiefe) for _ in range(200)]
    for it in range(budget//200):
        neu=[]
        for e in pool:
            t=treffer(e,Vs,Ts)
            if t>best[0]: best=(t,e)
            neu.append((t,e))
        neu.sort(key=lambda x:-x[0])
        elite=[e for _,e in neu[:40]]
        pool=list(elite)
        while len(pool)<200:
            if rng.random()<0.5:
                pool.append(rnd_expr(rng,maxtiefe))
            else:
                base=rng.choice(elite)
                pool.append(rnd_expr(rng,maxtiefe) if rng.random()<0.3 else
                            (rng.choice(BINOPS), base, rnd_expr(rng,2)))
    return best

print("="*72)
print("SUCHE: kuerzester arithmetischer Ausdruck")
print("="*72)
print("  Operatoren: + - * ^ & | >> << %   Terminale: v, Konstanten")
print("  Ziel: moeglichst viele der 81 Paare EXAKT treffen\n")

echte_paare=[(v, ziel[v]) for v in gueltig]
b_echt = suche(echte_paare, seed=1)
print(f"  ECHTE K1-1 Paare:      {b_echt[0]:>3} von {len(gueltig)} exakt getroffen"
      f"   (Ausdrucksgroesse {groesse(b_echt[1]) if b_echt[1] else 0})")

rng=random.Random(99)
kontroll=[]
for i in range(3):
    vs=rng.sample(range(N), len(gueltig))
    zufallspaare=[(v, rng.randrange(1<<32)) for v in vs]
    b=suche(zufallspaare, seed=10+i)
    kontroll.append(b[0])
    print(f"  ZUFALLS-Paare {i+1}:        {b[0]:>3} von {len(gueltig)} exakt getroffen"
          f"   (Ausdrucksgroesse {groesse(b[1]) if b[1] else 0})")

print()
print("="*72)
print("ERGEBNIS")
print("="*72)
print(f"  Echte Paare:   {b_echt[0]} Treffer")
print(f"  Zufallspaare:  {sum(kontroll)/len(kontroll):.1f} Treffer im Mittel")
print()
if b_echt[0] <= max(kontroll)+1:
    print("  -> Kein Unterschied zur Kontrollgruppe. Der Ausdruck, der die echten")
    print("     Paare am besten trifft, ist nicht besser als einer fuer zufaellige")
    print("     Paare. Die 81 Paare verhalten sich arithmetisch wie Zufall.")
else:
    print("  -> Echte Paare werden besser getroffen als Zufallspaare - hier lohnt")
    print("     genaueres Hinsehen.")
print()
print("  ZUR EINORDNUNG DES ERREICHTEN:")
print(f"  Ein Ausdruck der Groesse {groesse(b_echt[1]) if b_echt[1] else 0} trifft {b_echt[0]} von 81 Paaren.")
print(f"  Um alle 81 zu treffen, braeuchte es nach heutigem Stand ~81 Terme")
print(f"  (Lagrange). Der gefundene Ausdruck deckt {b_echt[0]/len(gueltig)*100:.1f} % ab.")
print()
print("  WICHTIG FUER DIE INTERPRETATION:")
print("  Bei 81 Paaren und Zielwerten aus 2^32 ist die Zufallstrefferquote")
print(f"  pro Paar 2^-32. Erwartete Zufallstreffer bei {400000} Versuchen:")
print(f"  {81*400000/2**32:.6f} - also praktisch null. Jeder Treffer ist echt,")
print("  aber er entsteht durch Anpassung an EINZELNE Punkte, nicht durch Struktur.")
