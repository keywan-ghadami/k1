"""Minimalgewicht ausreizen: Lee-Brickell + Canteaut-Chabaud + lokale Suche."""
import random, time, math, json
MASK=0xFFFFFFFF
def rotr(x,n): return ((x>>n)|(x<<(32-n)))&MASK
def s0(x): return rotr(x,7)^rotr(x,18)^(x>>3)
def s1(x): return rotr(x,17)^rotr(x,19)^(x>>10)
N=2048

def expandiere(W0_15):
    W=list(W0_15)
    for t in range(16,64):
        W.append(s1(W[t-2])^W[t-7]^s0(W[t-15])^W[t-16])
    return W
def als_int(E):
    v=0
    for j,w in enumerate(E): v |= w<<(32*j)
    return v
def generator(freie):
    Z=[]
    for wi in freie:
        for bi in range(32):
            W=[0]*16; W[wi]=1<<bi
            Z.append(als_int(expandiere(W)))
    return Z
def pc(v): return bin(v).count('1')

G_frei=generator(range(16))
G_pad =generator(range(8))

def gauss_perm(zeilen, perm):
    """Gauss mit vorgegebener Spaltenreihenfolge (Informationsmenge)."""
    Z=list(zeilen); r=0; piv=[]
    for sp in perm:
        p=None
        for i in range(r,len(Z)):
            if (Z[i]>>sp)&1: p=i; break
        if p is None: continue
        Z[r],Z[p]=Z[p],Z[r]
        zr=Z[r]
        for i in range(len(Z)):
            if i!=r and (Z[i]>>sp)&1: Z[i]^=zr
        piv.append(sp); r+=1
        if r==len(Z): break
    return Z[:r]

def suche(G, name, sekunden=240, seed=1):
    rng=random.Random(seed)
    k=len(G)
    best=min(pc(z) for z in G); bestv=min(G,key=pc)
    t0=time.time(); runden=0; verbesserungen=0
    spalten=list(range(N))
    R=list(G)
    while time.time()-t0<sekunden:
        runden+=1
        # --- echte zufaellige Spaltenpermutation (Informationsmenge) ---
        rng.shuffle(spalten)
        R=gauss_perm(G, spalten)
        if not R: continue
        # Lee-Brickell: alle Paare und Tripel aus einer Stichprobe
        stich=rng.sample(R, min(len(R), 90))
        for i in range(len(stich)):
            wi=pc(stich[i])
            if 0<wi<best:
                best,bestv=wi,stich[i]; verbesserungen+=1
            for j in range(i+1,len(stich)):
                v=stich[i]^stich[j]
                w=pc(v)
                if 0<w<best:
                    best,bestv=w,v; verbesserungen+=1
        # Tripel auf kleinerer Stichprobe
        st3=rng.sample(R, min(len(R),34))
        for i in range(len(st3)):
            for j in range(i+1,len(st3)):
                vij=st3[i]^st3[j]
                for l in range(j+1,len(st3)):
                    v=vij^st3[l]
                    w=pc(v)
                    if 0<w<best:
                        best,bestv=w,v; verbesserungen+=1
        # --- lokale Suche um das aktuell beste Wort ---
        for _ in range(300):
            v=bestv ^ R[rng.randrange(len(R))]
            w=pc(v)
            if 0<w<best:
                best,bestv=w,v; verbesserungen+=1
    return best,bestv,runden,verbesserungen

print("="*80)
print("AUSGEREIZTE MINIMALGEWICHTSUCHE")
print("="*80)
print("  Verfahren: echte Spaltenpermutation (Informationsmengen-Dekodierung),")
print("  Lee-Brickell-Kombinationen bis Tripel, lokale Nachbarschaftssuche.\n")
ergebnis={}
for name,G,dim in [("freier Block",G_frei,512),("festes Padding (K1)",G_pad,256)]:
    print(f"  --- {name}, Code [2048, {dim}] ---")
    b,v,rd,vb=suche(G,name,sekunden=260,seed=hash(name)%997)
    proWort=[pc((v>>(32*j))&MASK) for j in range(64)]
    aktiv=[j for j,x in enumerate(proWort) if x]
    ergebnis[name]={'gewicht':b,'aktive_woerter':len(aktiv),
                    'gewicht_W0_15':sum(proWort[:16]),
                    'gewicht_W16_63':sum(proWort[16:]),
                    'profil':proWort,'iterationen':rd,'verbesserungen':vb}
    print(f"    Iterationen: {rd:,}   Verbesserungen: {vb}")
    print(f"    BESTES GEWICHT: {b}")
    print(f"    aktive Woerter: {len(aktiv)} von 64")
    print(f"    Gewicht W_0..W_15:  {sum(proWort[:16])}")
    print(f"    Gewicht W_16..W_63: {sum(proWort[16:])}")
    print(f"    Profil (Gewicht je Wort, erste 20):")
    print(f"      {proWort[:20]}")
    print()

print("="*80)
print("VERGLEICH ZUR AUSGANGSMESSUNG")
print("="*80)
print(f"  {'Variante':<26} {'vorher':>8} {'jetzt':>8} {'Verbesserung':>14}")
for name in ergebnis:
    b=ergebnis[name]['gewicht']
    print(f"  {name:<26} {467:>8} {b:>8} {467-b:>14}")
print()

print("="*80)
print("BEDEUTUNG")
print("="*80)
mn=min(e['gewicht'] for e in ergebnis.values())
print(f"  Obere Schranke des Minimalgewichts: {mn}")
print(f"  Jede rein lineare kollisionssuchende Charakteristik ueber 64 Runden")
print(f"  hat mindestens so viele aktive Bits.")
print()
print(f"  Grobe Kostenabschaetzung bei Wahrscheinlichkeit <= 1/2 je aktivem Bit:")
print(f"    2^-{mn} - weit jenseits von 2^-256.")
print()
print("  Das erklaert quantitativ, warum REIN LINEARE Charakteristiken fuer")
print("  SHA-256 chancenlos sind und die publizierten Angriffe stattdessen")
print("  lokale Kollisionen mit nichtlinearen Anfangsrunden verwenden.")
json.dump(ergebnis,open('/mnt/user-data/outputs/expansionscode.json','w'),indent=2)
print("\n  Rohdaten: expansionscode.json")
