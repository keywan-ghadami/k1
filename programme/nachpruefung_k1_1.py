"""K1-1 erschoepfend: 2^16 Eingaben."""
import hashlib, numpy as np, itertools

N = 1 << 16
def tabelle(fuell=b'\x00'):
    d = np.zeros((N, 32), dtype=np.uint8)
    for v in range(N):
        m = fuell * 30 + v.to_bytes(2, 'big')
        d[v] = np.frombuffer(hashlib.sha256(m).digest(), dtype=np.uint8)
    return d

D = tabelle()
print("K1-1[0x00]: alle 65.536 Hashes berechnet.")

# ---- 'gueltig' = >=10 fuehrende Nullbits ----
top = (D[:, 0].astype(np.uint32) << 8) | D[:, 1]
gueltig = int((top < (1 << 6)).sum())          # 16 - 10 = 6 Restbits
print(f"\n[0.3] Werte mit >=10 fuehrenden Nullbits: {gueltig}  (behauptet 81) -> {gueltig==81}")
print(f"      Zufallserwartung: {N/1024:.1f}")

# ---- Satz E: Kollisionen ----
bits = np.unpackbits(D, axis=1)                # (65536, 256)
def koll(k):
    key = np.packbits(bits[:, :k], axis=1).tobytes()
    w = len(key)//N
    s = {key[i*w:(i+1)*w] for i in range(N)}
    return N - len(s)
print(f"\n[Satz E] Kollisionen (n - #verschiedene Werte):")
soll = {12:61440, 16:24092, 20:1978, 24:126, 28:8, 32:1, 40:0, 256:0}
for k in (12,16,20,24,28,32,40,256):
    c = koll(k)
    bel = N - (1<<k)*(1 - np.exp(-N/(1<<k)))
    print(f"   {k:3d} Bit: gemessen {c:6d}   behauptet {soll[k]:6d}  "
          f"{'OK' if c==soll[k] else 'ABWEICHUNG'}   Belegungsmodell {bel:.1f}")

# ---- Satz 9: ANF ueber alle 2^16 Eingaben ----
def moebius(f):
    step = 1
    while step < len(f):
        f = f.reshape(-1, 2*step)
        f[:, step:] ^= f[:, :step]
        f = f.reshape(-1)
        step *= 2
    return f
idx = np.arange(N, dtype=np.uint32)
grad_tab = np.array([bin(i).count('1') for i in range(N)], dtype=np.uint8)
mon, grade = [], []
for b in range(256):
    anf = moebius(bits[:, b].copy())
    m = int(anf.sum()); mon.append(m)
    grade.append(int(grad_tab[anf == 1].max()))
print(f"\n[Satz 9] ANF ueber alle 256 Ausgabebits:")
print(f"   Monome: min {min(mon)}  max {max(mon)}  (behauptet Bereich 32.540-32.840)")
print(f"   Grad:   min {min(grade)} max {max(grade)}  (behauptet 15-16)")
print(f"   Bit 0:  {mon[0]} Monome, Grad {grade[0]}  (behauptet 32.540 / Grad 16)"
      f" -> {mon[0]==32540}")
print(f"   Zufallserwartung 32.768; Mittel gemessen {np.mean(mon):.1f}")

# ---- Satz 11: Nichtlinearitaet, 12-Bit-Variante wie im Skript ----
NB = 12; n12 = 1 << NB
def tt12(p, bitpos=0):
    t = np.zeros(n12, dtype=np.uint8)
    for v in range(n12):
        d = hashlib.sha256(p*30 + v.to_bytes(2,'big')).digest()
        t[v] = (d[bitpos//8] >> (7-(bitpos % 8))) & 1
    return t
def nl(t):
    W = (1 - 2*t.astype(np.int32)); step = 1
    while step < len(W):
        W = W.reshape(-1, 2*step)
        a = W[:, :step].copy(); b = W[:, step:].copy()
        W[:, :step] = a+b; W[:, step:] = a-b
        W = W.reshape(-1); step *= 2
    return n12//2 - int(np.abs(W).max())//2
soll_nl = {'00':1924, 'FF':1925, 'AA':1927, '55':1929, '0F':1931}
print(f"\n[Satz 11] Nichtlinearitaet (12-Bit-Restriktion, wie in k1_transform.py):")
werte = {}
for k, p in [('00',b'\x00'), ('FF',b'\xff'), ('AA',b'\xaa'), ('55',b'\x55'), ('0F',b'\x0f')]:
    v = nl(tt12(p)); werte[k] = v
    print(f"   K1-1[0x{k}]: {v:5d}   behauptet {soll_nl[k]:5d}  "
          f"{'OK' if v==soll_nl[k] else 'ABWEICHUNG'}")
print(f"   paarweise verschieden: {len(set(werte.values()))==5}")
