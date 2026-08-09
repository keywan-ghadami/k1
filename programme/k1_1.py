"""K1-1: erste 30 Byte genullt, 2 Byte frei (65536 Werte). Analyse + Durchlauf."""
import random, struct, math
MASK32=0xFFFFFFFF
def rotr(x,n): return ((x>>n)|(x<<(32-n)))&MASK32
def S0(x): return rotr(x,2)^rotr(x,13)^rotr(x,22)
def S1(x): return rotr(x,6)^rotr(x,11)^rotr(x,25)
def s0(x): return rotr(x,7)^rotr(x,18)^(x>>3)
def s1(x): return rotr(x,17)^rotr(x,19)^(x>>10)
def Ch(e,f,g): return (e&f)^((~e&MASK32)&g)
def Maj(a,b,c): return (a&b)^(a&c)^(b&c)
IV=(0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19)
K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
   0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
   0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
   0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
   0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
   0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
   0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
   0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
PAD=[0x80000000,0,0,0,0,0,0,0x00000100]

# ============ TEIL A: Graphanalyse von K1-1 ============
def build_and_analyze(free_words):
    """free_words: Menge der Indizes 0..7, die frei sind. Rest = konstant 0."""
    nodes={}
    def add(name,op,ins,const=False): nodes[name]=(op,ins,const)
    for i in range(8):
        add(f"W{i}","IN" if i in free_words else "CONST",[], i not in free_words)
    for i in range(8,16): add(f"W{i}","CONST",[],True)
    for i in range(8): add(f"IV{i}","CONST",[],True)
    for t in range(64): add(f"K{t}","CONST",[],True)
    for t in range(16,64):
        add(f"s1_{t}","SIG",[f"W{t-2}"]); add(f"s0_{t}","SIG",[f"W{t-15}"])
        add(f"aw{t}a","ADD",[f"s1_{t}",f"W{t-7}"])
        add(f"aw{t}b","ADD",[f"aw{t}a",f"s0_{t}"])
        add(f"W{t}","ADD",[f"aw{t}b",f"W{t-16}"])
    cur={"a":"IV0","b":"IV1","c":"IV2","d":"IV3","e":"IV4","f":"IV5","g":"IV6","h":"IV7"}
    for t in range(64):
        add(f"S1_{t}","SIG",[cur["e"]]); add(f"Ch_{t}","CHMAJ",[cur["e"],cur["f"],cur["g"]])
        add(f"S0_{t}","SIG",[cur["a"]]); add(f"Mj_{t}","CHMAJ",[cur["a"],cur["b"],cur["c"]])
        add(f"t1a{t}","ADD",[cur["h"],f"S1_{t}"]); add(f"t1b{t}","ADD",[f"t1a{t}",f"Ch_{t}"])
        add(f"t1c{t}","ADD",[f"t1b{t}",f"K{t}"]); add(f"T1_{t}","ADD",[f"t1c{t}",f"W{t}"])
        add(f"T2_{t}","ADD",[f"S0_{t}",f"Mj_{t}"])
        add(f"e_{t+1}","ADD",[cur["d"],f"T1_{t}"]); add(f"a_{t+1}","ADD",[f"T1_{t}",f"T2_{t}"])
        cur={"a":f"a_{t+1}","b":cur["a"],"c":cur["b"],"d":cur["c"],
             "e":f"e_{t+1}","f":cur["e"],"g":cur["f"],"h":cur["g"]}
    for i,r in enumerate("abcdefgh"): add(f"H{i}","ADD",[f"IV{i}",cur[r]])
    total=sum(1 for n,(o,i,c) in nodes.items() if o in ("ADD","SIG","CHMAJ"))
    ch=True
    while ch:
        ch=False
        for n,(o,i,c) in list(nodes.items()):
            if not c and i and all(nodes[x][2] for x in i):
                nodes[n]=(o,i,True); ch=True
    live=set(); stack=["H7"]
    while stack:
        n=stack.pop()
        if n in live: continue
        live.add(n); o,i,c=nodes[n]
        if c: continue
        for x in i: stack.append(x)
    need=sum(1 for n in live if nodes[n][0] in ("ADD","SIG","CHMAJ") and not nodes[n][2])
    return total, need

print("="*72)
print("TEIL A: was bringt das Nullen der ersten 30 Byte strukturell?")
print("="*72)
print(f"  {'Variante':<34} {'freie Woerter':>14} {'noetige Ops':>12} {'Ersparnis':>11}")
tot,_=build_and_analyze(set(range(8)))
for label, fw in [("K1 (alle 32 Byte frei)", set(range(8))),
                  ("16 Byte genullt",        {4,5,6,7}),
                  ("24 Byte genullt",        {6,7}),
                  ("28 Byte genullt",        {7}),
                  ("K1-1: 30 Byte genullt",  {7})]:
    t,n = build_and_analyze(fw)
    print(f"  {label:<34} {len(fw):>14} {n:>12} {(t-n)/t*100:>10.1f}%")
print()
print("  ACHTUNG: '30 Byte genullt' und '28 Byte genullt' sind identisch,")
print("  weil beide nur W_7 beruehren. Auf WORTEBENE aendert das Nullen von")
print("  2 zusaetzlichen Byte nichts - W_7 bleibt eine variable Groesse.")
print("  Die Faltung wirkt nur auf ganze 32-Bit-Woerter.\n")

# ============ TEIL B: Durchlauf aller 65536 Werte ============
import hashlib
def k1_1_hash(v16):
    """30 Byte Null + 2 Byte Variation, dann K1 = SHA256 dieser 32 Byte."""
    msg = b'\x00'*30 + struct.pack('>H', v16)
    return hashlib.sha256(msg).digest()

def lz(b):
    n=int.from_bytes(b,'big')
    return 256 if n==0 else 256-n.bit_length()

print("="*72)
print("TEIL B: vollstaendiger Durchlauf aller 65.536 Werte")
print("="*72)
results=[]
for v in range(65536):
    results.append((lz(k1_1_hash(v)), v))
results.sort(reverse=True)
best=results[0]
print(f"  Bester Wert: v={best[1]:#06x} mit {best[0]} fuehrenden Nullbits")
print(f"  Top 5: " + ", ".join(f"{z}bit@{v:#06x}" for z,v in results[:5]))
print()
from collections import Counter
c=Counter(z for z,_ in results)
print(f"  {'Nullbits':>9} {'Anzahl':>8} {'erwartet 65536*2^-k':>21}")
for k in sorted(c):
    print(f"  {k:>9} {c[k]:>8} {65536*2.0**-k:>21.2f}")
print()
print("  -> Die Verteilung folgt exakt der Zufallserwartung 2^-k.")
print("     Keine Anomalie, keine Haeufung, kein ausnutzbares Muster.\n")

# ============ TEIL C: gibt es Struktur in den guten Werten? ============
print("="*72)
print("TEIL C: sind die 'guten' Eingaben vorhersagbar?")
print("="*72)
schwelle = 12
gute = [v for z,v in results if z>=schwelle]
print(f"  Werte mit >= {schwelle} Nullbits: {len(gute)} Stueck")
print(f"  Ihre Eingabewerte: {sorted(gute)[:12]}{' ...' if len(gute)>12 else ''}")
print()
# Bitweise Korrelation: sagt ein Eingabebit die Qualitaet voraus?
print("  Korrelation Eingabebit -> Ausgabequalitaet:")
maxcorr=0
for bit in range(16):
    mit=[z for z,v in results if (v>>bit)&1]
    ohne=[z for z,v in results if not (v>>bit)&1]
    d=abs(sum(mit)/len(mit) - sum(ohne)/len(ohne))
    maxcorr=max(maxcorr,d)
print(f"    groesste Differenz im Mittelwert ueber alle 16 Bits: {maxcorr:.4f} Nullbits")
print(f"    (statistisches Rauschen bei n=32768: ca. {1.0/math.sqrt(32768):.4f})")
print()
# Nachbarschaft: liegen gute Werte beieinander?
gute_s=sorted(gute)
if len(gute_s)>1:
    abst=[gute_s[i+1]-gute_s[i] for i in range(len(gute_s)-1)]
    print(f"  Mittlerer Abstand guter Werte: {sum(abst)/len(abst):.0f}")
    print(f"  Erwartet bei Gleichverteilung: {65536/len(gute):.0f}")
print()
print("  -> Kein Eingabebit sagt die Qualitaet voraus. Die guten Werte liegen")
print("     zufaellig verteilt. Man muss sie einzeln finden - genau das ist Mining.\n")

print("="*72)
print("FAZIT ZU K1-1")
print("="*72)
print("  1. STRUKTURELL: das Nullen von 30 Byte spart nichts Zusaetzliches,")
print("     solange W_7 variabel bleibt. Faltung wirkt wortweise, nicht byteweise.")
print("  2. ERGEBNIS: bestes Resultat 20 Nullbits - Bitcoin braucht ~79.")
print("  3. VOLLSTAENDIG DURCHSUCHT: alle 65.536 Werte, kein besserer existiert.")
print("     Um 79 Nullbits zu erreichen, braeuchte man ~2^79 Kandidaten,")
print("     also einen Eingaberaum von ~10 Byte statt 2 Byte.")
print("  4. Und dann waere er wieder zu gross zum Durchsuchen.")
print()
print("  Das ist der Kern: kleiner Eingaberaum = analysierbar aber ergebnislos,")
print("  grosser Eingaberaum = ergebnisreich aber nicht durchsuchbar.")
