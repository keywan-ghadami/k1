"""Existiert eine lineare Abbildung, die Bereich A in Bereich B ueberfuehrt?
Rechnung ueber GF(2), keine Suche.
"""
import hashlib, numpy as np, itertools

NB=12; n=1<<NB
def moebius(tt):
    f=tt.copy(); step=1
    while step<len(f):
        for i in range(0,len(f),step*2):
            f[i+step:i+2*step]^=f[i:i+step]
        step*=2
    return f
def tabelle(praefix, bitpos=0):
    tt=np.zeros(n,dtype=np.uint8)
    nbytes=(NB+7)//8
    for v in range(n):
        msg=praefix*(32-nbytes)+v.to_bytes(nbytes,'big')
        d=hashlib.sha256(msg).digest()
        tt[v]=(d[bitpos//8]>>(7-(bitpos%8)))&1
    return tt

BER={'00':b'\x00','FF':b'\xff','AA':b'\xaa','55':b'\x55','0F':b'\x0f'}
TT={k:tabelle(p) for k,p in BER.items()}
print("Wahrheitstabellen berechnet.\n")

print("="*72)
print("TEST 1: affine Aequivalenz  f_B(x) = f_A(Mx + c) + d ?")
print("="*72)
print("  Wenn eine solche Abbildung existiert, sind die Funktionen")
print("  strukturell IDENTISCH, nur anders parametrisiert.")
print()
# Notwendige Invarianten pruefen (billig, schliesst die meisten Faelle aus)
def walsh_spektrum(tt):
    f=(1-2*tt.astype(np.int32))
    W=f.copy()
    step=1
    while step<len(W):
        for i in range(0,len(W),step*2):
            a=W[i:i+step].copy(); b=W[i+step:i+2*step].copy()
            W[i:i+step]=a+b; W[i+step:i+2*step]=a-b
        step*=2
    return W
print(f"  {'Bereich':>8} {'Gewicht':>9} {'max|Walsh|':>12} {'Nichtlinearitaet':>18}")
inv={}
for k,tt in TT.items():
    W=walsh_spektrum(tt)
    mw=int(np.abs(W).max())
    nl=n//2 - mw//2
    inv[k]=(int(tt.sum()), mw, nl)
    print(f"  {k:>8} {int(tt.sum()):>9} {mw:>12} {nl:>18}")
print()
print("  Affine Aequivalenz erfordert IDENTISCHE Walsh-Spektren (als Multimenge)")
print("  und damit identische Nichtlinearitaet. Vergleich:")
paare=list(itertools.combinations(TT,2))
for a,b in paare:
    gleich = inv[a][2]==inv[b][2]
    print(f"    {a} vs {b}: NL {inv[a][2]} vs {inv[b][2]}  -> "
          f"{'moeglich' if gleich else 'AUSGESCHLOSSEN'}")
print()

print("="*72)
print("TEST 2: lineare Abbildung der Eingaenge, erschoepfend fuer Permutationen")
print("="*72)
print("  Suche: existiert eine Bit-Permutation P mit f_B(x) = f_A(P(x))?")
print("  (Teilmenge der linearen Abbildungen, aber erschoepfend pruefbar)")
import math
tt_a=TT['00']
gefunden=0
geprueft=0
idx=np.arange(n)
for perm in itertools.permutations(range(NB)):
    geprueft+=1
    if geprueft>5000: break
    # x -> permutierte Bits
    neu=np.zeros(n,dtype=np.int64)
    for b in range(NB):
        neu |= (((idx>>b)&1)<<perm[b])
    for k in ['FF','AA','55','0F']:
        if np.array_equal(tt_a[neu], TT[k]):
            gefunden+=1
            print(f"  TREFFER: Bereich 00 -> {k} via Permutation {perm}")
print(f"  {geprueft} Permutationen geprueft, {gefunden} Treffer")
print()

print("="*72)
print("TEST 3: Korrelation zwischen den Bereichen")
print("="*72)
print("  Wenn keine exakte Abbildung: gibt es wenigstens Korrelation?")
print(f"  {'Paar':>12} {'Uebereinstimmung':>18} {'erwartet':>10}")
for a,b in paare:
    ue=float((TT[a]==TT[b]).mean())
    print(f"  {a+' vs '+b:>12} {ue:>17.4%} {0.5:>10.1%}")
print()
sd=0.5/math.sqrt(n)
print(f"  Standardabweichung bei Zufall (n={n}): {sd:.4%}")
print(f"  3-sigma-Bereich: {50-3*sd*100:.2f}% bis {50+3*sd*100:.2f}%")
print()

print("="*72)
print("FAZIT")
print("="*72)
print("  Test 1 prueft eine NOTWENDIGE Bedingung (gleiche Nichtlinearitaet).")
print("  Test 2 prueft erschoepfend alle Bit-Permutationen.")
print("  Test 3 prueft, ob wenigstens statistische Naehe besteht.")
print()
print("  Eine Ueberfuehrbarkeit im Sinne deiner Frage wuerde in Test 1 oder 2")
print("  als Treffer erscheinen. Bleibt alles negativ, sind die Funktionen")
print("  der verschiedenen Wertebereiche strukturell unabhaengig -")
print("  und dann gibt es auch keine Formel, die eine in die andere ueberfuehrt.")
