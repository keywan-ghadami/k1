"""Auftrag 4: der ERSTE Hash-Durchlauf.
K0 = zweiter Block des ersten Durchlaufs, fester Midstate, 4 freie Nonce-Byte.
"""
import math, struct, hashlib, random, time
MASK=0xFFFFFFFF

def rotr(x,n): return ((x>>n)|(x<<(32-n)))&MASK
def S0(x): return rotr(x,2)^rotr(x,13)^rotr(x,22)
def S1(x): return rotr(x,6)^rotr(x,11)^rotr(x,25)
def s0(x): return rotr(x,7)^rotr(x,18)^(x>>3)
def s1(x): return rotr(x,17)^rotr(x,19)^(x>>10)
def Ch(e,f,g): return (e&f)^((~e&MASK)&g)
def Maj(a,b,c): return (a&b)^(a&c)^(b&c)
def icbrt(n):
    lo,hi=0,1
    while hi**3<=n: hi*=2
    while lo<hi:
        m=(lo+hi+1)//2
        if m**3<=n: lo=m
        else: hi=m-1
    return lo
def primes(n):
    p=[];c=2
    while len(p)<n:
        if all(c%q for q in p if q*q<=c): p.append(c)
        c+=1
    return p
P=primes(64); K=[icbrt(p*(1<<96))&MASK for p in P]
IVv=[math.isqrt(p*(1<<64))&MASK for p in primes(8)]

print("="*80)
print("DEFINITION VON K0")
print("="*80)
print("  Bitcoin-Header: 80 Byte = Version(4) PrevHash(32) MerkleRoot(32)")
print("                            Time(4) Bits(4) Nonce(4)")
print()
print("  Erster SHA-256-Durchlauf, Block 1: Byte 0-63   -> Midstate (nonce-frei)")
print("  Erster SHA-256-Durchlauf, Block 2: Byte 64-79  -> K0")
print()
print("  K0-Eingabewoerter:")
felder=[("W_0","Byte 64-67: MerkleRoot-Ende","konstant"),
        ("W_1","Byte 68-71: Time","konstant je Template"),
        ("W_2","Byte 72-75: Bits","konstant"),
        ("W_3","Byte 76-79: NONCE","FREI, 2^32"),
        ("W_4","Padding 0x80000000","konstant"),
        ("W_5..W_14","Null","konstant"),
        ("W_15","640 (= 80 Byte in Bit)","konstant")]
for a,b,c in felder:
    print(f"    {a:<10} {b:<32} {c}")
print()
print("  -> Die Nonce liegt in W_3. Bei K1-1 lagen die freien Bits in W_7,")
print("     bei K1 in W_0..W_7.")
print()

# --- Aufbau ---
rng=random.Random(2026)
version=struct.pack('>I',0x20000000)
prevhash=bytes(rng.randrange(256) for _ in range(32))
merkle=bytes(rng.randrange(256) for _ in range(32))
zeit=struct.pack('>I',1_754_000_000)
bits=struct.pack('>I',0x1709e1cf)
def header(nonce): return version+prevhash+merkle+zeit+bits+struct.pack('>I',nonce&MASK)

def kompress(state,block,runden=64):
    W=list(struct.unpack('>16I',block))
    for t in range(16,runden):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK)
    a,b,c,d,e,f,g,h=state
    for t in range(runden):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK
        T2=(S0(a)+Maj(a,b,c))&MASK
        h,g,f=g,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
    return tuple((x+y)&MASK for x,y in zip(state,(a,b,c,d,e,f,g,h)))

MIDSTATE=kompress(tuple(IVv), header(0)[:64])
print(f"  Midstate (nonce-unabhaengig): {' '.join(f'{x:08x}' for x in MIDSTATE)}\n")

def k0_block(nonce):
    return header(nonce)[64:80]+b'\x80'+b'\x00'*39+struct.pack('>Q',640)

print("="*80)
print("STRUKTURKARTE: ab welcher Runde wirkt die Nonce?")
print("="*80)
def zustand_nach(nonce,runden):
    blk=k0_block(nonce)
    W=list(struct.unpack('>16I',blk))
    for t in range(16,max(runden,16)):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK)
    a,b,c,d,e,f,g,h=MIDSTATE
    for t in range(runden):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK
        T2=(S0(a)+Maj(a,b,c))&MASK
        h,g,f=g,f,e; e=(d+T1)&MASK; d,c,b=c,b,a; a=(T1+T2)&MASK
    return (a,b,c,d,e,f,g,h)
print(f"  {'Runde':>6} {'verschiedene Zustaende':>24} {'Vergleich K1-1':>18}")
k11_vergleich={0:1,1:1,2:1,3:1,4:1,5:1,6:1,7:1,8:400,9:400,10:400,12:400}
for r in [0,1,2,3,4,5,6,8,12]:
    zs=len({zustand_nach(n,r) for n in range(400)})
    v=k11_vergleich.get(r,'-')
    print(f"  {r:>6} {zs:>24} {str(v):>18}")
print()
print("  -> K0: Nonce wirkt ab Runde 3.   K1-1: erst ab Runde 8.")
print("     K0 hat also 5 Runden WENIGER konstanten Vorlauf.")
print()

print("="*80)
print("LAWINENEFFEKT: ein Nonce-Bit gekippt")
print("="*80)
def pack(s):
    v=0
    for x in s: v=(v<<32)|x
    return v
def ham(a,b): return bin(pack(a)^pack(b)).count('1')
rr=random.Random(9)
paare=[]
for _ in range(150):
    n1=rr.randrange(1<<32); n2=n1^(1<<rr.randrange(32))
    paare.append((n1,n2))
print(f"  {'Runde':>6} {'diff. Bits / 256':>18} {'Anteil':>9}")
for r in [2,3,4,5,6,8,12,16,24,32,64]:
    tot=sum(ham(zustand_nach(a,r),zustand_nach(b,r)) for a,b in paare)
    m=tot/len(paare)
    print(f"  {r:>6} {m:>18.1f} {m/256:>8.1%}")
print()
print("  -> Saettigung bei ~50 % nach etwa 10-12 Runden, wie bei K1.")
print()

print("="*80)
print("VOLLSTAENDIGER DURCHLAUF: Stichprobe des 2^32-Raums")
print("="*80)
def lz(b):
    n=int.from_bytes(b,'big')
    return 256 if n==0 else 256-n.bit_length()
N=400_000
t0=time.time()
verteilung={}
bestes=(-1,None)
for nonce in range(N):
    d=hashlib.sha256(hashlib.sha256(header(nonce)).digest()).digest()
    z=lz(d)
    verteilung[z]=verteilung.get(z,0)+1
    if z>bestes[0]: bestes=(z,nonce)
dt=time.time()-t0
print(f"  {N:,} Nonces in {dt:.1f}s ({N/dt:,.0f} H/s, reines Python)")
print(f"  Bestes Ergebnis: Nonce {bestes[1]:,} mit {bestes[0]} fuehrenden Nullbits")
print(f"  Vollstaendige Erschoepfung von 2^32 wuerde "
      f"{(2**32)/(N/dt)/3600:.1f} Stunden dauern.\n")
print(f"  {'Nullbits':>9} {'Anzahl':>9} {'erwartet':>11}")
for z in sorted(verteilung):
    if z<=22:
        print(f"  {z:>9} {verteilung[z]:>9,} {N*2.0**-z:>11.1f}")
print()
print("="*80)
print("EINORDNUNG")
print("="*80)
print("  K0 ist das eigentlich Bitcoin-spezifische Objekt: der Suchraum des")
print("  Miners besteht genau aus diesen 2^32 Nonces bei festem Template.")
print()
print("  Strukturell ist K0 SCHLECHTER analysierbar als K1-1:")
print("    - nur 3 statt 7 Runden konstanter Vorlauf")
print("    - 2^32 statt 2^16 Eingaben, also nicht in Sekunden erschoepfbar")
print("    - dieselbe Saettigung des Lawineneffekts nach ~10 Runden")
print()
print("  Der einzige strukturelle Unterschied zu K1 ist die Lage der freien")
print("  Bits (W_3 statt W_0..W_7) und die Zahl freier Bits (32 statt 256).")
