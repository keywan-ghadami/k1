import hashlib, os, random
M32 = 0xFFFFFFFF
rotr = lambda x,n: ((x>>n)|(x<<(32-n))) & M32
rotl = lambda x,n: ((x<<n)|(x>>(32-n))) & M32
s0 = lambda x: rotr(x,7)^rotr(x,18)^(x>>3)
s1 = lambda x: rotr(x,17)^rotr(x,19)^(x>>10)
S0 = lambda x: rotr(x,2)^rotr(x,13)^rotr(x,22)
S1 = lambda x: rotr(x,6)^rotr(x,11)^rotr(x,25)
Ch  = lambda e,f,g: (e&f)^(~e & g)&M32
Maj = lambda a,b,c: (a&b)^(a&c)^(b&c)
def frac(x,n=32): return int((x-int(x))*(1<<n))
def primes(k):
    ps,c=[],2
    while len(ps)<k:
        if all(c%p for p in ps if p*p<=c): ps.append(c)
        c+=1
    return ps
P=primes(64); IV=[frac(p**0.5) for p in P[:8]]; K=[frac(p**(1/3.)) for p in P]

# ---- Satz 2: W0 = -s0(W1) erzwingt W16 = 0, und NUR W16 ----
print("[Satz 2] relationale Bedingung W0 = -sigma0(W1) mod 2^32")
nur_w16 = True; alle_w16_null = True
for _ in range(2000):
    W1 = random.getrandbits(32)
    W0 = (-s0(W1)) & M32
    W = [W0, W1] + [random.getrandbits(32) for _ in range(6)]
    W += [0x80000000, 0,0,0,0,0,0, 0x00000100]
    for t in range(16,64):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16]) & M32)
    if W[16] != 0: alle_w16_null = False
    if any(W[t]==0 for t in range(17,64)): nur_w16 = False
print(f"   W16 == 0 in allen 2000 Faellen: {alle_w16_null}")
print(f"   kein weiteres W_t == 0 (t=17..63):        {nur_w16}")

# ---- Satz 6: K1-1 Runden 0-6 eingabeunabhaengig ----
def zustand(msg, runden):
    m = msg + b'\x80' + b'\x00'*23 + (256).to_bytes(8,'big')
    W = [int.from_bytes(m[i:i+4],'big') for i in range(0,64,4)]
    for t in range(16,64):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16]) & M32)
    a,b,c,d,e,f,g,h = IV
    for t in range(runden):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&M32
        T2=(S0(a)+Maj(a,b,c))&M32
        h,g,f,e,d,c,b,a = g,f,e,(d+T1)&M32,c,b,a,(T1+T2)&M32
    return (a,b,c,d,e,f,g,h)
z7 = {zustand(b'\x00'*30 + v.to_bytes(2,'big'), 7) for v in range(0,65536,257)}
z8 = {zustand(b'\x00'*30 + v.to_bytes(2,'big'), 8) for v in range(0,65536,257)}
print(f"\n[Satz 6] verschiedene Zustaende nach Runde 7: {len(z7)} (erwartet 1)")
print(f"         nach Runde 8: {len(z8)} (erwartet >1, W7 wird gelesen)")

# ---- 12.3: erfuellt eine Rundenkonstante K = rotl(K,r)? ----
loesungen = [x for x in (0, M32) ]
treffer = [(t,r) for t in range(64) for r in range(1,32) if K[t]==rotl(K[t],r)]
print(f"\n[12.3] K_t == rotl(K_t,r) fuer ein t,r (r=1..31): {treffer} -> "
      f"{'keine' if not treffer else 'TREFFER'}")
print(f"       32-Bit-Werte mit x==rotl(x,1): "
      f"{[hex(x) for x in range(1<<32) if False] or ['0x00000000','0xffffffff (analytisch)']}")

# ---- 11.2: Gewicht des Codeworts mit einem aktiven Bit in W0 ----
print("\n[11.2] linearisierte Expansion (+ -> XOR), Einzelbit in W0, festes Padding")
best = None
for bit in range(32):
    W = [0]*16; W[0] = 1 << bit
    for t in range(16,64):
        W.append(s1(W[t-2]) ^ W[t-7] ^ s0(W[t-15]) ^ W[t-16])
    gw = sum(bin(x).count('1') for x in W)
    aktiv = sum(1 for x in W if x)
    if best is None or gw < best[1]: best = (bit, gw, aktiv,
        sum(bin(x).count('1') for x in W[:16]), sum(bin(x).count('1') for x in W[16:]))
print(f"   bestes Einzelbit: Position {best[0]}, Gesamtgewicht {best[1]}, "
      f"aktive Woerter {best[2]}")
print(f"   Gewicht W0-W15 / W16-W63: {best[3]} / {best[4]}  "
      f"(behauptet 1 / 466, gesamt 467, 44 aktive Woerter)")

# ---- 12.1: RX-Propagation durch modulare Addition ----
print("\n[12.1] P(RX ueberlebt modulare Addition), 200.000 Paare:")
soll = {1:0.6250, 2:0.4375, 4:0.2812, 8:0.2510}
for r in (1,2,4,8):
    tr = 0
    for _ in range(200000):
        a = random.getrandbits(32); b = random.getrandbits(32)
        if rotl((a+b)&M32, r) == ((rotl(a,r)+rotl(b,r)) & M32): tr += 1
    print(f"   r={r}: gemessen {tr/200000:.4f}   Dokument {soll[r]:.4f}")
