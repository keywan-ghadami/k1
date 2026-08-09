"""
Test der K1-Architektur (Revision 2.0) - Kernbehauptungen empirisch prüfen.

Strategie:
1. SHA-256 komplett neu implementieren, Konstanten aus Primzahlen selbst
   herleiten (keine auswendig gelernten Hex-Werte -> kein Abschreibfehler-Risiko).
2. Gegen hashlib validieren (bit-exakt).
3. Abschnitt 2 (Message-Schedule-Vereinfachung W19/W20) nachrechnen.
4. Abschnitt 3 (Zweierkomplement-Tabelle) nachrechnen.
5. Den eigentlichen Kernpunkt testen: Ist der interne Zustand nach ein paar
   Runden wirklich unabhängig von der Nonce (W3), wie Abschnitt 5 behauptet?
   -> Avalanche-Test: ein Nonce-Bit kippen, Hamming-Distanz pro Runde messen.
6. Realistische Zielverteilung: viele Nonces echt durchrechnen, Verteilung
   der führenden Nullbits zeigen.
"""
import math, struct, os, random, time, hashlib

MASK32 = 0xFFFFFFFF

# ---------- 1) Konstanten selbst herleiten (keine Hex-Literale aus dem Gedächtnis) ----------

def isqrt(n):
    return math.isqrt(n)

def icbrt(n):
    lo, hi = 0, 1
    while hi**3 <= n:
        hi *= 2
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid**3 <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo

def first_n_primes(n):
    primes = []
    c = 2
    while len(primes) < n:
        if all(c % p for p in primes if p * p <= c):
            primes.append(c)
        c += 1
    return primes

primes8, primes64 = first_n_primes(8), first_n_primes(64)

# frac(sqrt(p)) * 2^32  ==  isqrt(p * 2^64) mod 2^32   (2^64 ist eine Quadratzahl)
H0 = tuple(isqrt(p * (1 << 64)) & MASK32 for p in primes8)
# frac(cbrt(p)) * 2^32  ==  icbrt(p * 2^96) mod 2^32   (2^96 ist eine Kubikzahl)
K  = tuple(icbrt(p * (1 << 96)) & MASK32 for p in primes64)

expected_iv = (0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
               0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19)
print("[1] Hergeleiteter IV :", [hex(x) for x in H0])
print("    FIPS-180-4 IV    :", [hex(x) for x in expected_iv])
assert H0 == expected_iv
print("    -> IV stimmt exakt ueberein (selbst hergeleitet, nicht abgeschrieben).\n")

# ---------- 2) SHA-256 komplett implementieren ----------

def rotr(x, n): return ((x >> n) | (x << (32 - n))) & MASK32
def sig0_sched(x): return rotr(x,7)  ^ rotr(x,18) ^ (x >> 3)
def sig1_sched(x): return rotr(x,17) ^ rotr(x,19) ^ (x >> 10)
def big_sig0(x):   return rotr(x,2)  ^ rotr(x,13) ^ rotr(x,22)
def big_sig1(x):   return rotr(x,6)  ^ rotr(x,11) ^ rotr(x,25)
def ch(e,f,g):     return (e & f) ^ ((~e & MASK32) & g)
def maj(a,b,c):     return (a & b) ^ (a & c) ^ (b & c)

def compress(state, block):
    w = list(struct.unpack('>16I', block))
    for t in range(16, 64):
        w.append((sig1_sched(w[t-2]) + w[t-7] + sig0_sched(w[t-15]) + w[t-16]) & MASK32)
    a,b,c,d,e,f,g,h = state
    trace = [(a,b,c,d,e,f,g,h)]
    for t in range(64):
        T1 = (h + big_sig1(e) + ch(e,f,g) + K[t] + w[t]) & MASK32
        T2 = (big_sig0(a) + maj(a,b,c)) & MASK32
        h,g,f = g,f,e
        e = (d + T1) & MASK32
        d,c,b = c,b,a
        a = (T1 + T2) & MASK32
        trace.append((a,b,c,d,e,f,g,h))
    new_state = tuple((s + x) & MASK32 for s, x in zip(state, (a,b,c,d,e,f,g,h)))
    return new_state, w, trace

def sha256(msg: bytes) -> bytes:
    ml = len(msg) * 8
    padded = msg + b'\x80'
    while len(padded) % 64 != 56:
        padded += b'\x00'
    padded += struct.pack('>Q', ml)
    state = H0
    for i in range(0, len(padded), 64):
        state, _, _ = compress(state, padded[i:i+64])
    return b''.join(struct.pack('>I', x) for x in state)

print("[2] Validierung gegen hashlib ...")
for test in [b'', b'abc', b'The quick brown fox jumps over the lazy dog', os.urandom(137)]:
    mine, ref = sha256(test), hashlib.sha256(test).digest()
    assert mine == ref, f"MISMATCH bei {test[:20]!r}"
print("    -> Eigenimplementierung ist bit-identisch zu hashlib.sha256 auf allen Testvektoren.\n")

# ---------- 3) Bitcoin-Header aufbauen (80 Byte) ----------

rng = random.Random(1234)
version    = struct.pack('>I', 0x20000000)
prevhash   = bytes(rng.randrange(256) for _ in range(32))
merkleroot = bytes(rng.randrange(256) for _ in range(32))
time_field = struct.pack('>I', 1_754_000_000)
bits_field = struct.pack('>I', 0x1709e1cf)   # Groessenordnung realistisches nBits

def build_header(nonce_int: int) -> bytes:
    return version + prevhash + merkleroot + time_field + bits_field + struct.pack('>I', nonce_int & MASK32)

def chunk2_padded(nonce_int: int) -> bytes:
    tail = build_header(nonce_int)[64:80]
    return tail + b'\x80' + b'\x00'*39 + struct.pack('>Q', 640)  # 80 Byte = 640 Bit

# Sanity check: Chunk1 (Midstate) haengt NICHT von der Nonce ab
mid_x, _, _ = compress(H0, build_header(111)[:64])
mid_y, _, _ = compress(H0, build_header(999999)[:64])
assert mid_x == mid_y
print("[3] Midstate nach Chunk 1 ist nonce-unabhaengig: bestaetigt (trivial, Nonce liegt nur in Chunk 2).")

# End-zu-End Sanity check gegen hashlib fuer den vollen 2-Chunk-Header
nonce_probe = 777_777
ref = hashlib.sha256(build_header(nonce_probe)).digest()
mid, _, _ = compress(H0, build_header(nonce_probe)[:64])
final_state, w_probe, trace_probe = compress(mid, chunk2_padded(nonce_probe))
mine = b''.join(struct.pack('>I', x) for x in final_state)
assert mine == ref
print("    Voller 2-Chunk-Header (Chunk1+Chunk2) stimmt exakt mit hashlib ueberein.\n")

# ---------- 4) Abschnitt 2 des Dokuments: W19/W20-Vereinfachung ----------

print("[4] Nachrechnung Abschnitt 2 (Message-Schedule-Reduktion):")
w = w_probe
print(f"    W12 = {hex(w[12])}   W13 = {hex(w[13])}")
w19_voll     = (sig1_sched(w[17]) + w[12] + sig0_sched(w[4]) + w[3]) & MASK32
w19_reduziert= (sig1_sched(w[17])         + sig0_sched(w[4]) + w[3]) & MASK32
w20_voll     = (sig1_sched(w[18]) + w[13] + sig0_sched(w[5]) + w[4]) & MASK32
w20_reduziert= (sig1_sched(w[18])         + sig0_sched(w[5]) + w[4]) & MASK32
print(f"    W19: voll={hex(w19_voll)}  reduziert(Dok.)={hex(w19_reduziert)}  gleich={w19_voll==w19_reduziert}")
print(f"    W20: voll={hex(w20_voll)}  reduziert(Dok.)={hex(w20_reduziert)}  gleich={w20_voll==w20_reduziert}")
print("    -> Algebraisch korrekt, aber trivial: es wird nur ein bekannter Null-Summand weggelassen.")
print("       Jedes Synthese-Tool macht diese Konstantenfaltung automatisch (kein SAT/CDCL noetig).\n")

# ---------- 5) Abschnitt 3: Zweierkomplement-Tabelle ----------

print("[5] Nachrechnung Abschnitt 3 (Davies-Meyer / Zweierkomplement-Tabelle):")
claimed = ['0x95f61999','0x4498517b','0xc3910c8e','0x5ab00ac6',
           '0xaef1ad81','0x64fa9774','0xe07c2655','0xa41f32e7']
all_ok = True
for iv, c in zip(H0, claimed):
    computed = (~iv + 1) & MASK32
    ok = hex(computed) == c
    all_ok &= ok
    print(f"    IV={iv:#010x} -> berechnet {computed:#010x}, Dokument {c}, korrekt={ok}")
print(f"    -> Gesamte Tabelle korrekt: {all_ok}  (reine Modulo-Arithmetik, kein kryptografischer Shortcut).\n")

# ---------- 6) DER KERNTEST: Ist der Zustand wirklich unabhaengig von W3 (Nonce)? ----------
# Abschnitt 5 behauptet: der Schnittgraph/Beweis ist "vollstaendig frei von W3-Literalen".
# W3 = Nonce wird bereits in Kompressionsrunde t=3 direkt als Operand verwendet (T1 haengt
# von W[3] ab). Wir kippen EIN Bit der Nonce und messen die Hamming-Distanz des kompletten
# 256-Bit-Zustands (a..h) nach jeder der 64 Runden, gemittelt ueber viele Zufalls-Nonce-Paare.

def state_to_int(s):
    v = 0
    for x in s: v = (v << 32) | x
    return v

def hamming(s1, s2):
    return bin(state_to_int(s1) ^ state_to_int(s2)).count('1')

print("[6] KERNTEST: Lawineneffekt bei Nonce-Bit-Flip (widerlegt 'nonce-unabhaengiger Beweis'):")
trials_n, rng2 = 60, random.Random(999)
avg_hd = [0.0]*65
for _ in range(trials_n):
    na = rng2.randrange(0, 1<<32)
    nb = na ^ (1 << rng2.randrange(0,32))          # genau 1 Bit der Nonce gekippt
    mid_a,_,_ = compress(H0, build_header(na)[:64])
    mid_b,_,_ = compress(H0, build_header(nb)[:64])
    assert mid_a == mid_b                            # Chunk-1-Midstate identisch (korrekt)
    _,_,ta = compress(mid_a, chunk2_padded(na))
    _,_,tb = compress(mid_b, chunk2_padded(nb))
    for t in range(65):
        avg_hd[t] += hamming(ta[t], tb[t])
avg_hd = [x/trials_n for x in avg_hd]

print(f"    {'Runde t':>8} {'diff. Bits / 256 (Mittel)':>28} {'Anteil':>8}   Kommentar")
markers = {0:"vor jeder Verarbeitung", 3:"Runde, die W3 zuerst konsumiert",
           4:"eine Runde NACH W3-Eintritt"}
for t in [0,1,2,3,4,5,6,8,10,12,16,20,24,32,40,48,56,64]:
    note = markers.get(t, "")
    print(f"    {t:>8} {avg_hd[t]:>28.2f} {avg_hd[t]/256:>7.1%}   {note}")

print("\n    -> Bis Runde 3 exakt 0 Unterschied (W0..W2 sind nonce-unabhaengig: Merkle-Tail/Time/Bits).")
print("       Ab Runde 3 (W3=Nonce) beginnt die Divergenz sofort und saettigt binnen ~15-20 Runden")
print("       bei ~50% (Lawineneffekt). D.h. der Zustand IST spaetestens ab Runde ~20 eine hochgradig")
print("       nichtlineare Funktion JEDES einzelnen Nonce-Bits - das Gegenteil von 'frei von W3'.\n")

# ---------- 7) Realistische Zielverteilung ueber viele Nonces (mit hashlib, fuer Tempo) ----------

def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def leading_zero_bits(b: bytes) -> int:
    n = int.from_bytes(b, 'big')
    return len(b)*8 if n == 0 else len(b)*8 - n.bit_length()

print("[7] Verteilung ueber echte Nonce-Versuche (SHA256d, wie im echten Bitcoin-Mining):")
N = 500_000
t0 = time.time()
counts = {}
best = (-1, None)
for nonce in range(N):
    hdr = build_header(nonce)
    lz = leading_zero_bits(sha256d(hdr))
    counts[lz] = counts.get(lz, 0) + 1
    if lz > best[0]:
        best = (lz, nonce)
dt = time.time() - t0
print(f"    {N:,} Nonces in {dt:.2f}s durchgerechnet ({N/dt:,.0f} H/s, reines Python)")
print(f"    Bestes Ergebnis in dieser Stichprobe: Nonce={best[1]} mit {best[0]} fuehrenden Nullbits\n")
print(f"    {'fuehrende 0-Bits':>16} {'Anzahl':>10} {'Anteil':>10}  {'~2^-k erwartet':>16}")
for k in sorted(counts):
    if k <= 24:
        print(f"    {k:>16} {counts[k]:>10} {counts[k]/N:>9.3%}  {2.0**-k:>16.3%}")

# Vergleich mit dem echten aktuellen Bitcoin-Ziel (Difficulty, live abgefragt: siehe Antworttext)
difficulty = 126.23e12
expected_hashes = difficulty * (2**32)
bit_equiv = math.log2(expected_hashes)
print(f"\n    Aktuelle Bitcoin-Difficulty (~126,23 T) entspricht ~{bit_equiv:.1f} Bit gefordeter")
print(f"    Fuehrend-Null-Aequivalenz  ->  ca. 1 Treffer in {expected_hashes:.2e} Versuchen.")
print(f"    Unsere {N:,} Versuche sind dagegen statistisch bedeutungslos (Faktor {expected_hashes/N:.1e}).")
print("    Und selbst mit erschoepfender Suche: WELCHES Nonce erfolgreich ist, folgt keinem Muster,")
print("    das aus den nonce-unabhaengigen Feldern ablesbar waere (siehe Lawineneffekt oben).")

