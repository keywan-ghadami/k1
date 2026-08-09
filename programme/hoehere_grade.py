"""Beziehungen zwischen gueltigen Eingaben - jenseits von Grad 1.
Kernfrage: was kostet ein Test auf Beziehungen vom Grad d?
"""
import hashlib, struct, time, math, random, json
import numpy as np

print("="*82)
print("VORAB: was kostet ein Beziehungstest vom Grad d?")
print("="*82)
print("  Um eine Beziehung vom Grad d zwischen n=256 Eingabebits zu FINDEN,")
print("  braucht man mehr Stichproben als es Monome vom Grad <= d gibt.")
print("  Sonst hat das System trivial vollen Rang und sagt nichts aus.\n")
n=256
print(f"  {'Grad d':>7} {'Monome C(256,<=d)':>20} {'noetige gueltige Eingaben':>27}")
kum=0
monome={}
for d in range(0,5):
    kum+=math.comb(n,d)
    monome[d]=kum
    print(f"  {d:>7} {kum:>20,} {kum:>27,}")
print()
print("  Und jede gueltige Eingabe kostet 2^k Hashes bei Schwelle k Nullbits:\n")
print(f"  {'Schwelle':>9} " + " ".join(f"{'Grad '+str(d):>14}" for d in [1,2,3]))
for k in [20,32,64,79]:
    zeile=f"  {k:>9} "
    for d in [1,2,3]:
        kosten=monome[d]*2**k
        zeile+=f"{math.log2(kosten):>13.1f}b"
    print(zeile)
print()
print("  (Angabe als log2 der noetigen Hash-Auswertungen)")
print()
print("  -> Grad 2 bei Mining-Schwelle 79: 2^94 Hashes allein fuer die")
print("     Stichprobe. Das Bitcoin-Netzwerk hat in 17 Jahren 2^96 geschafft.")
print("     Grad 3 waere 2^100 - jenseits des Erreichbaren.")
print()
print("  DAS IST DIE EIGENTLICHE GRENZE: nicht die Analysemethode, sondern")
print("  die Beschaffung der Datenpunkte, auf denen sie arbeiten muesste.\n")

# ---------- gueltige Eingaben erzeugen ----------
SCHWELLE=20
print("="*82)
print(f"STICHPROBE: Eingaben mit >= {SCHWELLE} fuehrenden Nullbits")
print("="*82)
gefunden=[]; t0=time.time(); versuche=0
while len(gefunden)<200 and time.time()-t0<240:
    versuche+=1
    d=hashlib.sha256(versuche.to_bytes(32,'big')).digest()
    if d[0]==0 and d[1]==0 and d[2]<16:
        gefunden.append(int.from_bytes(versuche.to_bytes(32,'big'),'big'))
dt=time.time()-t0
print(f"  {versuche:,} Hashes in {dt:.0f}s -> {len(gefunden)} Treffer")
print(f"  erwartet: {versuche/2**SCHWELLE:.1f}\n")
E=gefunden; N=len(E)
rng=random.Random(4242)
Z=[rng.randrange(1<<256) for _ in range(N)]

def rang_gf2(V):
    B=[]
    for v in V:
        cur=v
        for b in B:
            if cur^b < cur: cur^=b
        if cur: B.append(cur); B.sort(reverse=True)
    return len(B)

print("="*82)
print("TEST A: Grad-1-Rang (linear)")
print("="*82)
rE, rZ = rang_gf2(E), rang_gf2(Z)
print(f"  gueltige Eingaben: Rang {rE} von max {min(N,256)}")
print(f"  Zufallseingaben:   Rang {rZ} von max {min(N,256)}")
print(f"  -> {'kein' if rE==min(N,256) else 'EIN'} linearer Zusammenhang")
print("  AUSSAGEKRAFT: schliesst NUR lineare Beziehungen aus.\n")

print("="*82)
print("TEST B: Grad-2-Rang - und warum er hier nichts sagen kann")
print("="*82)
print(f"  Monome vom Grad <=2: {monome[2]:,}")
print(f"  verfuegbare Stichproben: {N}")
print(f"  -> {monome[2]//max(N,1):,}-fach zu wenig.")
print("  Der Rang ist zwangslaeufig {N} = voll, unabhaengig von jeder Struktur.")
print("  Ein Grad-2-Test ist mit dieser Stichprobe PRINZIPIELL nicht moeglich.\n")

print("="*82)
print("TEST C: Abstands- und Verteilungsstruktur (grad-unabhaengig)")
print("="*82)
def paare(V,k=4000):
    rr=random.Random(1); out=[]
    for _ in range(k):
        i,j=rr.randrange(len(V)),rr.randrange(len(V))
        if i!=j: out.append(bin(V[i]^V[j]).count('1'))
    return out
for nm,V in [("gueltige Eingaben",E),("Zufallseingaben",Z)]:
    a=paare(V)
    mu=sum(a)/len(a); sd=(sum((x-mu)**2 for x in a)/len(a))**0.5
    print(f"  {nm:<22} Abstand {mu:>7.2f} +/- {sd:>5.2f}   "
          f"min {min(a):>3}  max {max(a):>3}")
print(f"  {'Theorie':<22} Abstand {128:>7.2f} +/- {8.0:>5.2f}\n")

print("="*82)
print("TEST D: sind Differenzen gueltiger Paare besonders?")
print("="*82)
print("  Nichtlinearer Test: erzeugt base ^ (m1^m2) haeufiger Nullen")
print("  als base ^ Zufallsdifferenz?\n")
rr=random.Random(7)
dE=[E[i]^E[j] for i in range(min(40,N)) for j in range(i+1,min(40,N))]
dZ=[rng.randrange(1<<256) for _ in range(len(dE))]
def probe(diffs,proben=60000):
    tr=0
    for _ in range(proben):
        b=rr.randrange(1<<256)
        m=(b ^ diffs[rr.randrange(len(diffs))]).to_bytes(32,'big')
        if hashlib.sha256(m).digest()[0]==0: tr+=1
    return tr,proben
tE,pn=probe(dE); tZ,_=probe(dZ)
erw=pn/256; sd=math.sqrt(pn*(1/256)*(255/256))
print(f"  {'Differenzquelle':<26} {'Treffer':>9} {'erwartet':>10} {'Sigma':>8}")
print(f"  {'aus gueltigen Paaren':<26} {tE:>9} {erw:>10.1f} {(tE-erw)/sd:>+8.2f}")
print(f"  {'Zufallsdifferenzen':<26} {tZ:>9} {erw:>10.1f} {(tZ-erw)/sd:>+8.2f}")
print()

print("="*82)
print("EHRLICHE EINORDNUNG")
print("="*82)
print("  WAS GEPRUEFT WURDE:")
print("    - lineare Beziehungen (Test A)")
print("    - Abstandsstruktur (Test C)")
print("    - Wirkung von Differenzen, nichtlinear (Test D)")
print()
print("  WAS NICHT GEPRUEFT WERDEN KONNTE:")
print("    - Beziehungen vom Grad >= 2. Grund ist NICHT die Methode,")
print("      sondern die Stichprobengroesse: es braeuchte mindestens")
print(f"      {monome[2]:,} gueltige Eingaben statt {N}.")
print()
print("  KEIN TEST BEWEIST DIE ABWESENHEIT VON STRUKTUR.")
print("  Jeder bestaetigt nur das Fehlen genau des Musters, nach dem er sucht.")
print()
print("  Der praktisch entscheidende Punkt ist aber die Kostenrechnung oben:")
print("  ein Grad-2-Test auf Mining-Niveau braucht 2^94 Hashes. Wer die")
print("  aufbringen kann, braucht keinen Angriff mehr - er kann direkt minen.")
