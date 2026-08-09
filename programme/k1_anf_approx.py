"""Exakte ANF statt Suche. Approximation durch Gradabschneidung.
Dann: Koeffizientenvergleich zwischen Wertebereichen.
"""
import struct, hashlib, numpy as np, math
from collections import Counter

def moebius(tt):
    f=tt.copy(); n=len(f); step=1
    while step<n:
        for i in range(0,n,step*2):
            f[i+step:i+2*step] ^= f[i:i+step]
        step*=2
    return f

def popcount_arr(n):
    return np.array([bin(i).count('1') for i in range(n)],dtype=np.int8)

def hashbit(msg, bit=0):
    d=hashlib.sha256(msg).digest()
    return (d[bit//8]>>(7-(bit%8)))&1

# ---------- Bereiche: nbits freie Bits am Ende ----------
def mach_daten(nbits, praefix=b'\x00', bitpos=0):
    n=1<<nbits
    nbytes=(nbits+7)//8
    tt=np.zeros(n,dtype=np.uint8)
    for v in range(n):
        tail=v.to_bytes(nbytes,'big')
        msg=praefix*(32-nbytes)+tail
        tt[v]=hashbit(msg,bitpos)
    return tt

print("="*74)
print("SCHRITT 1-4: exakte ANF und Approximation durch Gradabschneidung")
print("="*74)
print(f"  {'n Bits':>7} {'Monome':>9} {'von':>8} {'Grad':>6} {'Anteil':>8}")
anf_store={}
for nbits in [8,10,12,14,16]:
    tt=mach_daten(nbits)
    anf=moebius(tt)
    pc=popcount_arr(1<<nbits)
    mon=int(anf.sum())
    grad=int(pc[anf==1].max()) if mon else 0
    anf_store[nbits]=(anf,pc)
    print(f"  {nbits:>7} {mon:>9} {1<<nbits:>8} {grad:>6} {mon/(1<<nbits):>7.1%}")
print()
print("  Erwartung fuer eine Zufallsfunktion: 50% der Monome, Grad = n")
print()

print("="*74)
print("GENAUIGKEIT BEI GRADABSCHNEIDUNG  (n = 16 Bit)")
print("="*74)
anf,pc = anf_store[16]
tt16 = mach_daten(16)
n=1<<16
print(f"  {'Grad <= d':>10} {'Terme':>10} {'Genauigkeit':>13} {'ueber Zufall':>14}")
for d in [0,1,2,3,4,6,8,12,16]:
    maske = (pc<=d)
    anf_kurz = anf.copy(); anf_kurz[~maske]=0
    terme=int(anf_kurz.sum())
    # Rueckwaerts: ANF -> Wahrheitstabelle (Moebius ist selbstinvers)
    rekon = moebius(anf_kurz)
    genau = float((rekon==tt16).mean())
    print(f"  {d:>10} {terme:>10} {genau:>12.4%} {genau-0.5:>13.4%}")
print()
print("  -> Ein Polynom vom Grad <= d approximiert das Ausgabebit mit dieser")
print("     Genauigkeit. Grad 16 ist exakt (100%), aber so gross wie die Tabelle.")
print()

print("="*74)
print("SCHRITT 5: KOEFFIZIENTENVERGLEICH ZWISCHEN WERTEBEREICHEN")
print("="*74)
BEREICHE={
 'praefix_00': b'\x00',
 'praefix_FF': b'\xff',
 'praefix_AA': b'\xaa',
}
anfs={}
NB=12
for name,pref in BEREICHE.items():
    tt=mach_daten(NB, praefix=pref)
    anfs[name]=moebius(tt)
    print(f"  {name}: {int(anfs[name].sum())} Monome von {1<<NB}")
print()
pc12=popcount_arr(1<<NB)
print("  Uebereinstimmung der Koeffizienten, nach Grad aufgeschluesselt:")
print(f"  {'Grad':>6} {'Terme moegl.':>14} {'in allen 3 gleich':>19} {'erwartet bei Zufall':>21}")
namen=list(anfs)
for d in range(0,7):
    idx=np.where(pc12==d)[0]
    if len(idx)==0: continue
    gleich=int(np.sum((anfs[namen[0]][idx]==anfs[namen[1]][idx]) &
                      (anfs[namen[1]][idx]==anfs[namen[2]][idx])))
    erwartet=len(idx)*0.25    # 3 unabh. Bits gleich: 2/8 = 0.25
    print(f"  {d:>6} {len(idx):>14} {gleich:>19} {erwartet:>21.1f}")
print()
print("  Bei Zufall stimmen 3 unabhaengige Bits mit W'keit 1/4 ueberein.")
print("  Liegt der gemessene Wert deutlich darueber, gibt es gemeinsame Struktur.")
print()

print("="*74)
print("NIEDRIGGRADIGE TERME IM DETAIL")
print("="*74)
print("  Grad 0 (Konstante) und Grad 1 (lineare Terme) pro Bereich:")
for name in namen:
    a=anfs[name]
    konst=int(a[0])
    lin=[i for i in np.where(pc12==1)[0] if a[i]]
    lin_bits=[int(math.log2(i)) for i in lin]
    print(f"    {name}: konstant={konst}, lineare Terme an Bitpositionen {sorted(lin_bits)}")
print()
print("  Wenn dieselben Bitpositionen in allen Bereichen linear auftauchen,")
print("  waere das uebertragbare Struktur.")
