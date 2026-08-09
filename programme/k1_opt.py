"""Optimierung der Fitness-Auswertung. Benchmark alt vs neu."""
import struct, hashlib, numpy as np, time

N=65536
ZIEL=np.array([int.from_bytes(hashlib.sha256(b'\x00'*30+struct.pack('>H',v)).digest()[:4],'big')
               for v in range(N)],dtype=np.uint32)
idx=np.random.default_rng(1).permutation(N)[:N//2]
ZT=ZIEL[idx]

# ================= ALT =================
GEW=np.array([1.0/(i+1) for i in range(32)]); GEW/=GEW.sum()
def bits_of64(x):
    x=x.astype(np.uint64)
    return ((x[:,None]>>np.arange(31,-1,-1,dtype=np.uint64)[None,:])&np.uint64(1)).astype(np.int8)
BZ_alt=bits_of64(ZT)
def fitness_alt(pred):
    pb=bits_of64(pred); zb=BZ_alt
    richtig=(pb==0)&(zb==0); falsch=(pb==0)&(zb!=0)
    s=((richtig*GEW[None,:]).sum(axis=1)-(falsch*GEW[None,:]).sum(axis=1)).mean()
    lauf=np.zeros(len(pred)); lebt=np.ones(len(pred),dtype=bool)
    for i in range(32):
        lebt&=richtig[:,i]; lauf+=lebt
    return s+0.3*lauf.mean()

# ================= NEU =================
# 1) Lauflaenge uebereinstimmender FUEHRENDER NULLEN in EINER Operation:
#    Beide muessen 0 sein -> betrachte (pred | ziel). Fuehrende Nullen davon
#    = Zahl der Positionen, an denen BEIDE Null sind, ab Bit 0.
#    clz via float-Exponent-Trick, vollstaendig vektorisiert.
def clz32(x):
    """Count leading zeros fuer uint32, vektorisiert."""
    xf=x.astype(np.float64)
    out=np.full(x.shape,32,dtype=np.int32)
    nz=x!=0
    out[nz]=31-np.floor(np.log2(xf[nz])).astype(np.int32)
    return out

# 2) Positionsgewichte via 16-Bit-Lookup: zwei Haelften statt 32 Spalten
def make_lut(gewichte, hi):
    """LUT[w] = Summe der Gewichte der Nullbits in w (16 Bit)."""
    lut=np.zeros(1<<16)
    g=gewichte[0:16] if hi else gewichte[16:32]
    for w in range(1<<16):
        s=0.0
        for i in range(16):
            if not (w>>(15-i))&1: s+=g[i]
        lut[w]=s
    return lut
print("Baue Lookup-Tabellen ...")
LUT_HI=make_lut(GEW,True); LUT_LO=make_lut(GEW,False)

def null_gewicht(x):
    """Summe der Positionsgewichte aller Nullbits in x."""
    return LUT_HI[(x>>np.uint32(16))] + LUT_LO[x & np.uint32(0xFFFF)]

# richtige Nullen = Nullbits in (pred | ziel)
# falsche Nullen  = Nullbits in pred, die in ziel Einsen sind = Nullbits von (pred | ~ziel)
def fitness_neu(pred):
    beide_null = pred | ZT                 # Nullbits hier = beide waren 0
    falsch_null = pred | (~ZT)             # Nullbits hier = pred 0, ziel 1
    s = (null_gewicht(beide_null) - null_gewicht(falsch_null)).mean()
    lauf = clz32(beide_null).mean()
    return s + 0.3*lauf

# ---------- Korrektheitspruefung ----------
rng=np.random.default_rng(5)
print("\nKorrektheitspruefung (alt vs neu):")
ok=True
for _ in range(5):
    p=rng.integers(0,1<<32,size=len(ZT),dtype=np.uint32)
    a=fitness_alt(p); b=fitness_neu(p)
    print(f"  alt {a:.8f}   neu {b:.8f}   Differenz {abs(a-b):.2e}")
    ok &= abs(a-b)<1e-9
print(f"  identisch: {ok}\n")

# ---------- Benchmark ----------
p=rng.integers(0,1<<32,size=len(ZT),dtype=np.uint32)
t0=time.perf_counter()
for _ in range(20): fitness_alt(p)
t_alt=(time.perf_counter()-t0)/20
t0=time.perf_counter()
for _ in range(200): fitness_neu(p)
t_neu=(time.perf_counter()-t0)/200
print("="*66)
print("BENCHMARK")
print("="*66)
print(f"  alt: {t_alt*1000:>8.2f} ms pro Auswertung")
print(f"  neu: {t_neu*1000:>8.2f} ms pro Auswertung")
print(f"  Beschleunigung: {t_alt/t_neu:.1f}x")
print()
print(f"  Bei Population 2000: alt {t_alt*2000:.1f}s je Generation")
print(f"                       neu {t_neu*2000:.1f}s je Generation")
print(f"  In 300 Sekunden: alt {300/(t_alt*2000):.0f} Generationen, "
      f"neu {300/(t_neu*2000):.0f} Generationen")
print()
print("  Weitere Hebel (nicht in diesem Benchmark):")
print("   - Subsampling: Fitness auf 4096 statt 32768 Werten -> nochmal 8x")
print("     (Rauschen steigt, aber fuer Selektion reicht es)")
print("   - Ausdruckscache: Eliten nicht neu auswerten -> ~10-15 %")
print("   - uint32 statt uint64 durchgehend -> halbe Speicherbandbreite")
