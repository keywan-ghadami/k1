"""K1-1 Praedikat: 81 gueltige Werte akzeptieren, 65455 ablehnen.
Minimierung als Schaltung. Kontrollgruppe: 81 ZUFAELLIGE Werte.
Wenn K1-1 besser komprimiert als Zufall -> Struktur. Sonst nicht.
"""
import struct, hashlib, random
from itertools import combinations

N=65536; NV=16
def lz(b):
    n=int.from_bytes(b,'big'); return 256 if n==0 else 256-n.bit_length()

print("Bestimme die gueltigen Werte ...")
qual=[]
for v in range(N):
    msg=b'\x00'*30+struct.pack('>H',v)
    qual.append(lz(hashlib.sha256(msg).digest()))
SCHWELLE=10
onset=sorted(v for v in range(N) if qual[v]>=SCHWELLE)
print(f"  {len(onset)} gueltige Werte (>= {SCHWELLE} Nullbits)\n")

# ---------- Cube-Darstellung: (mask, value) - Bits in mask sind fixiert ----------
def cube_covers(cube, v):
    m,val = cube
    return (v & m) == val

def expand(minterm, offset_set):
    """Maximal expandieren: Bits freigeben, solange kein Off-Set-Punkt gedeckt wird."""
    m = (1<<NV)-1
    val = minterm
    # Bits in zufaelliger Reihenfolge probieren (Espresso-Heuristik)
    order = list(range(NV)); random.shuffle(order)
    for b in order:
        nm = m & ~(1<<b)
        nval = val & nm
        # pruefen ob der groessere Cube einen Off-Set-Punkt deckt
        bad=False
        free_bits=[i for i in range(NV) if not (nm>>i)&1]
        # alle Punkte des Cubes durchgehen
        for combo in range(1<<len(free_bits)):
            p=nval
            for j,fb in enumerate(free_bits):
                if (combo>>j)&1: p |= (1<<fb)
            if p in offset_set:
                bad=True; break
        if not bad:
            m, val = nm, nval
    return (m, val)

def minimize(onset_list):
    onset_set=set(onset_list)
    offset_set=set(range(N))-onset_set
    cubes=[]
    for mt in onset_list:
        cubes.append(expand(mt, offset_set))
    # Greedy Set Cover
    uncovered=set(onset_list); chosen=[]
    while uncovered:
        best=None; bestcov=set()
        for cb in cubes:
            cov={v for v in uncovered if cube_covers(cb,v)}
            if len(cov)>len(bestcov):
                best, bestcov = cb, cov
        if not bestcov: break
        chosen.append(best); uncovered -= bestcov
    return chosen

def literals(cube):
    m,_=cube
    return bin(m).count('1')

random.seed(2026)
print("="*72)
print("MINIMIERUNG: K1-1 Praedikat")
print("="*72)
cover = minimize(onset)
lits = [literals(c) for c in cover]
print(f"  Produktterme im minimalen Cover: {len(cover)}")
print(f"  Literale gesamt:                 {sum(lits)}")
print(f"  Mittlere Literale pro Term:      {sum(lits)/len(lits):.2f} von {NV}")
print(f"  Groesster Cube deckt:            {max(2**(NV-l) for l in lits)} Werte")
print()

# ---------- KONTROLLGRUPPE: 81 zufaellige Werte ----------
print("="*72)
print("KONTROLLGRUPPE: 81 ZUFAELLIG gewaehlte Werte")
print("="*72)
ergebnisse=[]
for trial in range(5):
    rnd_on = sorted(random.sample(range(N), len(onset)))
    cov_r = minimize(rnd_on)
    l_r=[literals(c) for c in cov_r]
    ergebnisse.append((len(cov_r), sum(l_r)))
    print(f"  Versuch {trial+1}: {len(cov_r)} Terme, {sum(l_r)} Literale, "
          f"{sum(l_r)/len(l_r):.2f} Lit/Term")
mt=sum(e[0] for e in ergebnisse)/len(ergebnisse)
ml=sum(e[1] for e in ergebnisse)/len(ergebnisse)
print(f"\n  Mittelwert Zufall: {mt:.1f} Terme, {ml:.1f} Literale")
print()

print("="*72)
print("VERGLEICH - das ist die Antwort auf deine Frage")
print("="*72)
print(f"  {'':<28} {'Terme':>8} {'Literale':>10}")
print(f"  {'K1-1 (81 gueltige Werte)':<28} {len(cover):>8} {sum(lits):>10}")
print(f"  {'Zufall (81 Werte, Mittel)':<28} {mt:>8.1f} {ml:>10.1f}")
print()
diff_t = (mt-len(cover))/mt*100
diff_l = (ml-sum(lits))/ml*100
print(f"  K1-1 komprimiert um {diff_t:+.1f} % (Terme) bzw. {diff_l:+.1f} % (Literale)")
print("  gegenueber einer zufaelligen Wertemenge gleicher Groesse.")
print()
if abs(diff_t) < 10 and abs(diff_l) < 10:
    print("  BEFUND: kein signifikanter Unterschied. Die 81 gueltigen Werte")
    print("  verhalten sich bei der Logikminimierung wie 81 zufaellige Werte.")
    print("  Unter maximaler Einschraenkung wird KEINE Struktur sichtbar.")
else:
    print("  BEFUND: signifikanter Unterschied - hier lohnt genaueres Hinsehen.")
print()

print("="*72)
print("WAS DIE MINIMIERUNG KONKRET GELIEFERT HAT")
print("="*72)
print("  Groesste gefundene Cubes (Bits: X = frei, 0/1 = fixiert):")
srt=sorted(cover, key=lambda c: literals(c))[:6]
for cb in srt:
    m,val=cb
    s="".join('X' if not (m>>b)&1 else str((val>>b)&1) for b in range(NV-1,-1,-1))
    n_deckt=sum(1 for v in onset if cube_covers(cb,v))
    print(f"    {s}   deckt {n_deckt} gueltige Werte")
print()
print("  Ein Cube mit k freien Bits deckt 2^k Eingaben. Deckt er nur 1 gueltigen")
print("  Wert, ist er faktisch ein Tabelleneintrag - genau das, was du")
print("  ausschliessen wolltest. Zaehlung:")
einzeln=sum(1 for cb in cover if sum(1 for v in onset if cube_covers(cb,v))==1)
print(f"    Cubes, die genau 1 gueltigen Wert decken: {einzeln} von {len(cover)}")
print(f"    Cubes, die mehrere decken:                {len(cover)-einzeln}")
