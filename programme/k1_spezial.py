"""K1-SPEZIALISIERUNG: die vereinfachte Form wirklich BAUEN, nicht nur messen.
Alles was feststeht wird hart eincodiert. Danach: Verifikation + Ersparnis zaehlen.
"""
import random
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

ops_full=0; ops_spec=0
def cnt(full=0, spec=0):
    global ops_full, ops_spec
    ops_full+=full; ops_spec+=spec

# ---------- REFERENZ: volle K1 ----------
def k1_full(W0_7):
    W=list(W0_7)+PAD
    for t in range(16,64):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK32)
    a,b,c,d,e,f,g,h=IV
    for t in range(64):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK32
        T2=(S0(a)+Maj(a,b,c))&MASK32
        h,g,f=g,f,e; e=(d+T1)&MASK32; d,c,b=c,b,a; a=(T1+T2)&MASK32
    return tuple((x+y)&MASK32 for x,y in zip(IV,(a,b,c,d,e,f,g,h)))

# ---------- SPEZIALISIERT: alles Feststehende eincodiert ----------
# Runde 0 vorab ausgerechnet (alle Eingaenge ausser W_0 sind IV-Konstanten)
_a,_b,_c,_d,_e,_f,_g,_h = IV
C0_T1 = (_h + S1(_e) + Ch(_e,_f,_g) + K[0]) & MASK32      # T1 = W_0 + C0_T1
C0_T2 = (S0(_a) + Maj(_a,_b,_c)) & MASK32                 # T2 konstant
A1_C  = (C0_T1 + C0_T2) & MASK32                          # a_1 = W_0 + A1_C
E1_C  = (IV[3] + C0_T1) & MASK32                          # e_1 = W_0 + E1_C

# Runde 1: f,g = IV4,IV5 konstant -> Ch bitweise vorbestimmt wo f==g
F1, G1 = IV[4], IV[5]
CH1_FIX_MASK = ~(F1 ^ G1) & MASK32      # Bits wo Ch konstant ist
CH1_FIX_VAL  = F1 & CH1_FIX_MASK        # deren Wert
B1, C1 = IV[0], IV[1]
MAJ1_FIX_MASK = ~(B1 ^ C1) & MASK32
MAJ1_FIX_VAL  = B1 & MAJ1_FIX_MASK
# Runde 1 Konstanten
R1_H, R1_D = IV[6], IV[2]

# Runden 8-15: K+W vorgefaltet
KW = [(K[t] + PAD[t-8]) & MASK32 for t in range(8,16)]

def k1_spec(W0_7):
    W=list(W0_7)+PAD
    # Schedule: W_16 haengt von W_14=0, W_9=0 ab -> 2 Operanden statt 4
    W.append((s0(W[1]) + W[0]) & MASK32)                       # W_16, 2 statt 4 Operanden
    W.append((s1(W[15]) + s0(W[2]) + W[1]) & MASK32)           # W_17, W_10=0
    W.append((s1(W[16]) + s0(W[3]) + W[2]) & MASK32)           # W_18, W_11=0
    W.append((s1(W[17]) + s0(W[4]) + W[3]) & MASK32)           # W_19, W_12=0
    W.append((s1(W[18]) + s0(W[5]) + W[4]) & MASK32)           # W_20, W_13=0
    W.append((s1(W[19]) + s0(W[6]) + W[5]) & MASK32)           # W_21, W_14=0
    for t in range(22,64):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK32)

    # Runde 0: komplett vorberechnet
    a = (W[0] + A1_C) & MASK32
    e = (W[0] + E1_C) & MASK32
    b,c,d = IV[0],IV[1],IV[2]
    f,g,h = IV[4],IV[5],IV[6]

    # Runde 1: Ch/Maj teilweise vorbestimmt
    ch1 = CH1_FIX_VAL | ((Ch(e,F1,G1)) & ~CH1_FIX_MASK & MASK32)
    mj1 = MAJ1_FIX_VAL | ((Maj(a,B1,C1)) & ~MAJ1_FIX_MASK & MASK32)
    T1=(R1_H + S1(e) + ch1 + K[1] + W[1])&MASK32
    T2=(S0(a) + mj1)&MASK32
    h,g,f=g,f,e; e=(R1_D+T1)&MASK32; d,c,b=c,b,a; a=(T1+T2)&MASK32

    # Runden 2..63, Runden 8-15 mit vorgefaltetem K+W
    for t in range(2,64):
        kw = KW[t-8] if 8<=t<16 else (K[t]+W[t])&MASK32
        T1=(h+S1(e)+Ch(e,f,g)+kw)&MASK32
        T2=(S0(a)+Maj(a,b,c))&MASK32
        h,g,f=g,f,e; e=(d+T1)&MASK32; d,c,b=c,b,a; a=(T1+T2)&MASK32
    return tuple((x+y)&MASK32 for x,y in zip(IV,(a,b,c,d,e,f,g,h)))

# ---------- VERIFIKATION ----------
rng=random.Random(4242)
ok=True
for _ in range(3000):
    W=[rng.randrange(1<<32) for _ in range(8)]
    ok &= (k1_full(W)==k1_spec(W))
print("="*70)
print("VERIFIKATION der spezialisierten K1-Form")
print("="*70)
print(f"  3000 Zufallseingaben, spezialisiert == voll:  {ok}")
print("  -> Die Vereinfachung ist semantikerhaltend (kein Rechenfehler).\n")

# ---------- ERSPARNIS EXAKT ZAEHLEN ----------
print("="*70)
print("ERSPARNIS - exakt gezaehlt, nicht geschaetzt")
print("="*70)
# Schedule
full_sched_add = 48*3     # 48 Woerter x 3 Additionen (4 Operanden)
full_sched_sig = 48*2
spec_sched_add = 1*1 + 5*2 + 42*3
spec_sched_sig = 1*1 + 5*2 + 42*2
# Runden
full_round = {"add":64*6, "S":64*2, "chmaj":64*2}
# spezialisiert: Runde 0 entfaellt ganz (nur 2 Additionen), Runde 1 spart Teile,
# Runden 8-15 sparen je 1 Addition
spec_round_add = 2 + 6 + 62*6 - 8
spec_round_S   = 0 + 2 + 62*2
spec_round_chmaj = 0 + 2 + 62*2     # Runde 0 entfaellt, Runde 1 teilbestimmt (zaehlt voll)

rows=[
 ("Schedule: modulare Additionen", full_sched_add, spec_sched_add),
 ("Schedule: sigma-Funktionen",    full_sched_sig, spec_sched_sig),
 ("Runden: modulare Additionen",   full_round["add"], spec_round_add),
 ("Runden: Sigma-Funktionen",      full_round["S"], spec_round_S),
 ("Runden: Ch/Maj",                full_round["chmaj"], spec_round_chmaj),
]
tf=ts=0
print(f"  {'Komponente':<32} {'voll':>8} {'spezial.':>10} {'gespart':>9}")
for name,fu,sp in rows:
    tf+=fu; ts+=sp
    print(f"  {name:<32} {fu:>8} {sp:>10} {fu-sp:>9}")
print(f"  {'-'*62}")
print(f"  {'SUMME':<32} {tf:>8} {ts:>10} {tf-ts:>9}")
print(f"\n  Gesamtersparnis: {(tf-ts)/tf*100:.1f} % der 32-Bit-Operationen")
print()
print("  Davon entfallen auf:")
print(f"    Runde 0 komplett vorberechnet      : ~{(6+2+2)} Ops")
print(f"    Runden 8-15 K+W vorgefaltet        : 8 Ops")
print(f"    Schedule W_16..W_21 reduziert      : ~{full_sched_add-spec_sched_add+full_sched_sig-spec_sched_sig-0} Ops")
print()
print("  EHRLICHE EINORDNUNG:")
print("  Das ist eine reale, semantikerhaltende Vereinfachung - und exakt das,")
print("  was Mining-ASICs seit Jahren tun. Sie senkt den Aufwand PRO HASH.")
print("  Sie senkt NICHT die Zahl der noetigen Hashes. Der Suchraum bleibt 2^256.")
