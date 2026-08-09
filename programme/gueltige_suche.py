"""Gueltige K1-Eingaben erzeugen und auf Struktur untersuchen.
Frage: gibt es Beziehungen zwischen Eingaben, die viele Nullen erzeugen?
"""
import hashlib, struct, time, math, random, json
import numpy as np

def lz(b):
    n=int.from_bytes(b,'big')
    return 256 if n==0 else 256-n.bit_length()

SCHWELLE=20
print("="*80)
print("SCHRITT 1: gueltige Eingaben erzeugen")
print("="*80)
print(f"  K1 = SHA-256 auf 32 Byte. Gesucht: Eingaben mit >= {SCHWELLE}")
print(f"  fuehrenden Nullbits. Erwartete Trefferrate: 2^-{SCHWELLE}\n")
gefunden=[]
t0=time.time(); versuche=0
ZIEL=180
while len(gefunden)<ZIEL and time.time()-t0<300:
    for _ in range(200000):
        versuche+=1
        m=versuche.to_bytes(32,'big')
        d=hashlib.sha256(m).digest()
        if d[0]==0 and d[1]==0 and (d[2]>>(24-SCHWELLE+16))==0:
            z=lz(d)
            if z>=SCHWELLE:
                gefunden.append((int.from_bytes(m,'big'), z))
                if len(gefunden)>=ZIEL: break
    if len(gefunden)>=ZIEL: break
dt=time.time()-t0
print(f"  {versuche:,} Hashes in {dt:.0f}s ({versuche/dt:,.0f} H/s)")
print(f"  Gefunden: {len(gefunden)} Eingaben mit >= {SCHWELLE} Nullbits")
print(f"  Erwartet: {versuche/2**SCHWELLE:.1f}")
print(f"  Beste: {max(z for _,z in gefunden)} Nullbits\n")

E=[m for m,_ in gefunden]
N=len(E)

# ---------- Zufallskontrolle: gleich viele beliebige Eingaben ----------
rng=random.Random(4242)
Z=[rng.randrange(1<<256) for _ in range(N)]

def rang_gf2(vektoren, bits=256):
    """Rang der Menge ueber GF(2)."""
    B=[]
    for v in vektoren:
        cur=v
        for b in B:
            if cur ^ b < cur: cur ^= b
        if cur: B.append(cur); B.sort(reverse=True)
    return len(B)

print("="*80)
print("TEST 1: GF(2)-RANG - existiert eine lineare Beziehung?")
print("="*80)
rE=rang_gf2(E); rZ=rang_gf2(Z)
print(f"  {'Menge':<28} {'Elemente':>10} {'Rang':>8} {'max moeglich':>14}")
print(f"  {'gueltige Eingaben':<28} {N:>10} {rE:>8} {min(N,256):>14}")
print(f"  {'Zufallseingaben':<28} {N:>10} {rZ:>8} {min(N,256):>14}")
print()
if rE==min(N,256):
    print("  -> VOLLER RANG. Keine lineare Beziehung zwischen den gueltigen")
    print("     Eingaben. Sie spannen den maximal moeglichen Raum auf.")
else:
    print(f"  -> Rangdefekt {min(N,256)-rE}: es gibt lineare Abhaengigkeiten!")
print()

print("="*80)
print("TEST 2: paarweise Hamming-Abstaende")
print("="*80)
def abstaende(V, maxp=4000):
    rr=random.Random(1); out=[]
    for _ in range(maxp):
        i,j=rr.randrange(len(V)),rr.randrange(len(V))
        if i!=j: out.append(bin(V[i]^V[j]).count('1'))
    return out
aE=abstaende(E); aZ=abstaende(Z)
for nm,a in [("gueltige Eingaben",aE),("Zufallseingaben",aZ)]:
    mu=sum(a)/len(a); sd=(sum((x-mu)**2 for x in a)/len(a))**0.5
    print(f"  {nm:<24} Mittel {mu:>7.2f}  Stdabw {sd:>6.2f}  "
          f"min {min(a):>4}  max {max(a):>4}")
print(f"  {'Theorie (Zufall)':<24} Mittel {128:>7.2f}  Stdabw {math.sqrt(64):>6.2f}")
print()
print("  -> Bei 256 Bit ist der erwartete Abstand 128 mit Stdabw 8.")
print()

print("="*80)
print("TEST 3: Bitpositions-Bias")
print("="*80)
def bias(V):
    cnt=[0]*256
    for v in V:
        for b in range(256):
            cnt[b]+=(v>>b)&1
    return [c/len(V) for c in cnt]
bE=bias(E); bZ=bias(Z)
se=0.5/math.sqrt(N)
maxE=max(abs(x-0.5) for x in bE); maxZ=max(abs(x-0.5) for x in bZ)
print(f"  {'Menge':<24} {'max |Bias|':>12} {'in Sigma':>10}")
print(f"  {'gueltige Eingaben':<24} {maxE:>12.4f} {maxE/se:>10.2f}")
print(f"  {'Zufallseingaben':<24} {maxZ:>12.4f} {maxZ/se:>10.2f}")
print(f"\n  Rauschgrenze bei n={N}: {se:.4f}")
print(f"  Bei 256 geprueften Positionen ist ein Wert um 3 Sigma zu erwarten.\n")

print("="*80)
print("TEST 4: Nachbarschaftsstruktur - liegen gueltige Eingaben zusammen?")
print("="*80)
def naechster_nachbar(V):
    out=[]
    for i,v in enumerate(V):
        best=999
        for j,w in enumerate(V):
            if i==j: continue
            d=bin(v^w).count('1')
            if d<best: best=d
        out.append(best)
    return out
nE=naechster_nachbar(E[:120]); nZ=naechster_nachbar(Z[:120])
print(f"  {'Menge':<24} {'mittl. NN-Abstand':>19} {'min':>6}")
print(f"  {'gueltige Eingaben':<24} {sum(nE)/len(nE):>19.2f} {min(nE):>6}")
print(f"  {'Zufallseingaben':<24} {sum(nZ)/len(nZ):>19.2f} {min(nZ):>6}")
print()

print("="*80)
print("TEST 5: sind DIFFERENZEN gueltiger Eingaben besonders?")
print("="*80)
print("  Idee: wenn m1 und m2 beide gueltig sind, ist m1^m2 dann eine")
print("  besondere Differenz? Test: erzeugt m3 ^ (m1^m2) haeufiger")
print("  gueltige Ausgaben als eine Zufallsdifferenz?\n")
rr=random.Random(7)
def teste_differenz(diffs, label, proben=40000):
    treffer=0
    for _ in range(proben):
        base=rr.randrange(1<<256)
        d=diffs[rr.randrange(len(diffs))]
        m=(base ^ d).to_bytes(32,'big')
        h=hashlib.sha256(m).digest()
        if h[0]==0: treffer+=1          # >= 8 Nullbits
    return treffer, proben
echte_diffs=[E[i]^E[j] for i in range(0,40) for j in range(i+1,40)]
zufalls_diffs=[rng.randrange(1<<256) for _ in range(len(echte_diffs))]
tE,pE=teste_differenz(echte_diffs,"echt")
tZ,pZ=teste_differenz(zufalls_diffs,"zufall")
erw=pE/256
sd=math.sqrt(pE*(1/256)*(255/256))
print(f"  {'Differenzquelle':<28} {'Treffer':>9} {'erwartet':>10} {'Sigma':>8}")
print(f"  {'aus gueltigen Paaren':<28} {tE:>9} {erw:>10.1f} {(tE-erw)/sd:>+8.2f}")
print(f"  {'Zufallsdifferenzen':<28} {tZ:>9} {erw:>10.1f} {(tZ-erw)/sd:>+8.2f}")
print()

print("="*80)
print("FAZIT")
print("="*80)
print("  Alle fuenf Tests vergleichen gegen eine Kontrollgruppe gleicher Groesse.")
print()
print("  WAS DIESE ANALYSE KANN: lineare Beziehungen, Abstandsstruktur,")
print("  Positionsbias und Differenzeneffekte nachweisen.")
print()
print("  WAS SIE NICHT KANN: eine Struktur finden, die erst bei sehr vielen")
print("  Punkten sichtbar wird. Mit ~180 Punkten aus 2^256 ist die Stichprobe")
print("  extrem duenn. Eine Beziehung, die etwa jeden 2^40-ten gueltigen Wert")
print("  verbindet, waere hier unsichtbar.")
print()
print("  Das ist die prinzipielle Grenze: um Struktur zwischen gueltigen")
print("  Eingaben zu finden, braucht man viele gueltige Eingaben - und die")
print("  zu erzeugen kostet genau so viel wie das Mining selbst.")
json.dump({'schwelle':SCHWELLE,'gefunden':len(gefunden),'versuche':versuche,
           'rang_echt':rE,'rang_zufall':rZ},
          open('/mnt/user-data/outputs/gueltige_eingaben.json','w'),indent=2)
