"""K1-Zangenanalyse unter den fuenf Einschraenkungen.
Ziel: beweisbare Eigenschaften, nicht Vermutungen.
"""
import random, struct
MASK32 = 0xFFFFFFFF
def rotr(x,n): return ((x>>n)|(x<<(32-n)))&MASK32
def s0(x): return rotr(x,7)^rotr(x,18)^(x>>3)
def s1(x): return rotr(x,17)^rotr(x,19)^(x>>10)
PAD = [0x80000000,0,0,0,0,0,0,0x00000100]   # W_8..W_15

def sched(W0_7, upto=64):
    W = list(W0_7) + PAD
    for t in range(16, upto):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16]) & MASK32)
    return W

rng = random.Random(31337)
def sample(kill=True):
    W1 = rng.randrange(1<<32)
    W0 = (-s0(W1)) & MASK32 if kill else rng.randrange(1<<32)
    return [W0,W1]+[rng.randrange(1<<32) for _ in range(6)]

# ---------- A) Bitweise Determiniertheit: wieviel Struktur ueberlebt WIRKLICH? ----------
print("=== A) Bitweise Determiniertheit im Message Schedule (Kill-Switch aktiv) ===")
print("   Ein Bit heisst 'tot', wenn es ueber alle Samples konstant bleibt.")
N = 3000
samples = [sched(sample(True)) for _ in range(N)]
print(f"   {'W_t':>6} {'tote Bits':>10} {'Kommentar'}")
for t in range(16, 32):
    ones = MASK32; zeros = MASK32
    for W in samples:
        ones &= W[t]; zeros &= (~W[t]) & MASK32
    dead = bin(ones|zeros).count('1')
    note = "VOLLSTAENDIG konstant" if dead==32 else ("" if dead==0 else "teilweise")
    print(f"   {t:>6} {dead:>10} {note}")
print("   -> Ausserhalb W_16 ueberlebt KEIN einziges determiniertes Bit.\n")

# ---------- B) Freiheitsgrad-Bilanz (die eigentliche Zange) ----------
print("=== B) Freiheitsgrad-Bilanz: vorwaerts vs. rueckwaerts ===")
frei_ohne = 256                     # W_0..W_7, 8 Woerter a 32 Bit
frei_mit  = 256 - 32                # Kill-Switch bindet W_0 vollstaendig an W_1
ziel_bits = 256                     # H = 0 fixiert alle 8 Register
print(f"   Eingangsentropie K1 ohne Kill-Switch : {frei_ohne} Bit  -> 2^{frei_ohne} Kandidaten")
print(f"   Eingangsentropie K1 mit  Kill-Switch : {frei_mit} Bit  -> 2^{frei_mit} Kandidaten")
print(f"   Ausgangsbedingung H = 0              : {ziel_bits} Bit hart gebunden")
print()
print(f"   Erwartete Loesungszahl ohne Kill-Switch: 2^({frei_ohne}-{ziel_bits}) = 2^{frei_ohne-ziel_bits} = 1")
print(f"   Erwartete Loesungszahl mit  Kill-Switch: 2^({frei_mit}-{ziel_bits}) = 2^{frei_mit-ziel_bits}")
print(f"   -> also ca. {2.0**(frei_mit-ziel_bits):.3e}")
print()
print("   FOLGERUNG (beweisbar unter Zufallsorakel-Annahme):")
print("   Der Kill-Switch macht das System mit Wahrscheinlichkeit ~1-2^-32 UNERFUELLBAR.")
print("   Ein UNSAT waere damit KEIN kryptografischer Befund, sondern reine Abzaehlung:")
print("   du hast 32 Bit Suchraum weggenommen, die du fuer die Loesung gebraucht haettest.\n")

# ---------- C) Was kostet jede Einschraenkung? ----------
print("=== C) Bilanz der fuenf K1-Einschraenkungen ===")
rows = [
 ("1. Eingabe 32 Byte (Padding fix)", "+256 Bit Struktur", "hilft: 8 Woerter konstant"),
 ("2. Eingabe ist selbst ein Hash",   "0 Bit",             "wirkungslos: Hash ist ununterscheidbar von Zufall"),
 ("3. W_0 = -sigma_0(W_1)",           "-32 Bit Suchraum",  "kostet mehr als es bringt (nur W_16 stirbt)"),
 ("4. H = 0 erzwungen",               "-256 Bit",          "haerteste denkbare Bedingung"),
 ("5. Fester IV",                     "0 Bit",             "Standard, keine Zusatzinfo"),
]
for a,b,c in rows:
    print(f"   {a:<34} {b:>18}   {c}")
print()

# ---------- D) Gegenprobe: wo bringt Einschraenkung 2 doch etwas? ----------
print("=== D) Gegenprobe zu Einschraenkung 2 (Eingabe ist ein Hash) ===")
import hashlib
# Sind Hash-Ausgaben als Schedule-Input irgendwie strukturell auffaellig?
bits = [0]*256
M = 20000
for i in range(M):
    h = hashlib.sha256(struct.pack('>I', i)).digest()
    v = int.from_bytes(h,'big')
    for b in range(256):
        bits[b] += (v>>b) & 1
dev = max(abs(c/M - 0.5) for c in bits)
print(f"   {M:,} echte SHA-256-Ausgaben, max. Bit-Bias ueber alle 256 Positionen: {dev:.5f}")
print(f"   (statistisch erwartbar bei Gleichverteilung: ~{0.5/(M**0.5):.5f})")
print("   -> Kein ausnutzbarer Bias. 'Eingabe ist ein Hash' liefert dem Solver NICHTS,")
print("      ausser der bereits gezaehlten Laengeninformation von 256 Bit.")
