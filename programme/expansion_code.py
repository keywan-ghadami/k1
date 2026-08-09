"""Auftrag 5: linearisierte Nachrichtenexpansion als GF(2)-Code.
Minimalgewicht ist untere Schranke fuer lineare kollisionssuchende
Charakteristiken.
"""
import random, time, math
import numpy as np
MASK=0xFFFFFFFF

def rotr(x,n): return ((x>>n)|(x<<(32-n)))&MASK
def s0(x): return rotr(x,7)^rotr(x,18)^(x>>3)
def s1(x): return rotr(x,17)^rotr(x,19)^(x>>10)

print("="*80)
print("DER LINEARISIERTE CODE")
print("="*80)
print("  Die echte Expansion nutzt modulare Addition (nicht GF(2)-linear).")
print("  Die LINEARISIERUNG ersetzt + durch XOR:")
print("     W_t = sigma1(W_{t-2}) ^ W_{t-7} ^ sigma0(W_{t-15}) ^ W_{t-16}")
print()
print("  Das ist die Standardnaeherung fuer lineare Charakteristiken.")
print("  Ihr Minimalgewicht ist eine UNTERE SCHRANKE fuer die Zahl aktiver")
print("  Bits jeder linearen kollisionssuchenden Charakteristik.\n")

def expandiere_lin(W0_15):
    W=list(W0_15)
    for t in range(16,64):
        W.append(s1(W[t-2])^W[t-7]^s0(W[t-15])^W[t-16])
    return W

def gewicht(W):
    return sum(bin(w).count('1') for w in W)

# ---------- Generatormatrix ----------
def generator(freie_woerter, pad=None):
    """Zeilen = Bilder der Einheitsvektoren. Liefert (Zeilen als int, Laenge)."""
    zeilen=[]
    for wi in freie_woerter:
        for bi in range(32):
            W=[0]*16
            if pad:
                for i,v in pad.items(): W[i]=v
            W[wi]=1<<bi
            E=expandiere_lin(W)
            # Codewort als 2048-Bit-Zahl
            v=0
            for j,w in enumerate(E): v |= w<<(32*j)
            zeilen.append(v)
    return zeilen

print("="*80)
print("CODEPARAMETER")
print("="*80)
G_frei = generator(range(16))
G_pad  = generator(range(8))          # W_8..W_15 = 0 im linearen Anteil
print(f"  {'Variante':<38} {'Dimension':>10} {'Laenge':>8}")
print(f"  {'freier Block (publizierter Fall)':<38} {len(G_frei):>10} {2048:>8}")
print(f"  {'festes Padding (K1)':<38} {len(G_pad):>10} {2048:>8}")
print()
print("  -> Bei K1 hat der Code Dimension 256 statt 512. Das Ergebnis ist")
print("     daher nicht aus dem publizierten Fall ableitbar.\n")

def pc(v): return bin(v).count('1')

# ---------- Gewichtsverteilung der Basisvektoren ----------
print("="*80)
print("GEWICHT DER BASISVEKTOREN")
print("="*80)
for name,G in [("freier Block",G_frei),("festes Padding",G_pad)]:
    gew=[pc(z) for z in G]
    print(f"  {name:<20} min {min(gew):>5}  max {max(gew):>5}  "
          f"Mittel {sum(gew)/len(gew):>7.1f}")
print()

# ---------- Informationsmengen-Dekodierung (obere Schranke) ----------
def gauss_gf2(zeilen):
    """Zeilenstufenform, liefert Pivotpositionen."""
    Z=list(zeilen); piv=[]
    r=0
    for spalte in range(2048):
        p=None
        for i in range(r,len(Z)):
            if (Z[i]>>spalte)&1: p=i; break
        if p is None: continue
        Z[r],Z[p]=Z[p],Z[r]
        for i in range(len(Z)):
            if i!=r and (Z[i]>>spalte)&1: Z[i]^=Z[r]
        piv.append(spalte); r+=1
        if r==len(Z): break
    return Z[:r], piv

def isd_schranke(G, versuche, seed, maxkomb=3):
    """Informationsmengen-Dekodierung: zufaellige Permutation, Gauss,
       dann kleine Kombinationen der Basiszeilen pruefen."""
    rng=random.Random(seed)
    best=10**9; bestv=None
    n=len(G)
    for v in range(versuche):
        # zufaellige Spaltenreihenfolge simulieren durch Zeilenmischung
        Z=list(G); rng.shuffle(Z)
        R,_=gauss_gf2(Z)
        for z in R:
            w=pc(z)
            if 0<w<best: best,bestv=w,z
        # kleine Kombinationen
        for _ in range(400):
            k=rng.randrange(2,maxkomb+1)
            acc=0
            for _ in range(k): acc ^= R[rng.randrange(len(R))]
            w=pc(acc)
            if 0<w<best: best,bestv=w,acc
    return best,bestv

print("="*80)
print("MINIMALGEWICHT - obere Schranken per Informationsmengen-Dekodierung")
print("="*80)
t0=time.time()
for name,G in [("freier Block (dim 512)",G_frei),("festes Padding (dim 256)",G_pad)]:
    b,v=isd_schranke(G, versuche=25, seed=hash(name)%999)
    # Verteilung des Gewichts auf die 64 Woerter
    proWort=[pc((v>>(32*j))&MASK) for j in range(64)]
    aktiv=[j for j,x in enumerate(proWort) if x]
    print(f"\n  {name}")
    print(f"    bestes gefundenes Gewicht: {b}")
    print(f"    aktive Woerter: {len(aktiv)} von 64  (Indizes {aktiv[0]}..{aktiv[-1]})")
    print(f"    Gewicht in W_0..W_15:  {sum(proWort[:16])}")
    print(f"    Gewicht in W_16..W_63: {sum(proWort[16:])}")
print(f"\n  (Rechenzeit {time.time()-t0:.0f}s)")
print()

print("="*80)
print("EINORDNUNG")
print("="*80)
print("  Das gefundene Gewicht ist eine OBERE SCHRANKE fuer das Minimalgewicht.")
print("  Die exakte Bestimmung ist fuer einen [2048,256]-Code NP-schwer;")
print("  Verfahren wie Brouwer-Zimmermann liefern engere Schranken, brauchen")
print("  aber erheblich mehr Rechenzeit.")
print()
print("  BEDEUTUNG: jede lineare kollisionssuchende Charakteristik ueber die")
print("  volle Rundenzahl hat mindestens so viele aktive Bits. Bei einer")
print("  differentiellen Wahrscheinlichkeit von hoechstens 2^-1 je aktivem Bit")
print("  ergibt das eine grobe Kostenschranke.")
print()
print("  WICHTIGE EINSCHRAENKUNG: die Linearisierung ist eine NAEHERUNG.")
print("  Die echte Expansion nutzt modulare Addition; Uebertraege koennen")
print("  Differenzen sowohl daempfen als auch verstaerken. Die Schranke gilt")
print("  streng nur fuer rein lineare Charakteristiken.")
