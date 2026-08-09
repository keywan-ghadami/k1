"""K1 weiter kuerzen: Abhaengigkeitskegel am AUSGANG.
Fuer den Target-Vergleich braucht man nicht alle 8 Register.
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

def schedule(W0_7):
    W=list(W0_7)+PAD
    for t in range(16,64):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK32)
    return W

def k1_full(W0_7):
    W=schedule(W0_7)
    a,b,c,d,e,f,g,h=IV
    for t in range(64):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK32
        T2=(S0(a)+Maj(a,b,c))&MASK32
        h,g,f=g,f,e; e=(d+T1)&MASK32; d,c,b=c,b,a; a=(T1+T2)&MASK32
    return tuple((x+y)&MASK32 for x,y in zip(IV,(a,b,c,d,e,f,g,h)))

print("="*72)
print("ABHAENGIGKEITSKEGEL AM AUSGANG")
print("="*72)
print("  Bitcoin prueft Hash < Target. Die fuehrenden Nullen liegen (little-endian)")
print("  im LETZTEN 32-Bit-Wort des Digests, also H_7 = IV_7 + h_64.")
print("  Frage: welche Operationen braucht man fuer h_64 WIRKLICH?\n")
print("  Register-Shift rueckwaerts verfolgt:")
print("    h_64 = g_63 = f_62 = e_61 = d_60 + T1_60")
print("  -> h_64 haengt NUR von d_60 und T1_60 ab.")
print("  -> In den Runden 61,62,63 wird h_64 nur noch DURCHGESCHOBEN.")
print("     Alle a/b/c/d-Berechnungen dieser Runden sind fuer H_7 irrelevant.\n")

# Verifikation: h_64 nur aus Runde 60 berechnen
def h64_kurz(W0_7):
    W=schedule(W0_7)
    a,b,c,d,e,f,g,h=IV
    for t in range(61):                      # nur bis Runde 60 (inkl.)
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK32
        T2=(S0(a)+Maj(a,b,c))&MASK32
        h,g,f=g,f,e; e=(d+T1)&MASK32; d,c,b=c,b,a; a=(T1+T2)&MASK32
    return (IV[7] + e) & MASK32              # e_61 wandert bis h_64 durch

rng=random.Random(31)
ok=True
for _ in range(3000):
    W=[rng.randrange(1<<32) for _ in range(8)]
    ok &= (k1_full(W)[7] == h64_kurz(W))
print(f"  VERIFIKATION: H_7 aus Kurzform == H_7 aus voller K1:  {ok}")
print("  -> Runden 61,62,63 sind fuer den Target-Test vollstaendig ueberfluessig.\n")

print("="*72)
print("WAS DAS EINSPART")
print("="*72)
# Ops pro Runde: 6 Additionen, 2 Sigma, 2 Ch/Maj = 10
# Runde 61,62,63 komplett weg: aber Schedule W_61..W_63 auch
print("  Runden 61-63 entfallen komplett:          3 x 10 =  30 Ops")
print("  Schedule W_61,W_62,W_63 entfallen:        3 x  5 =  15 Ops")
print("  Feed-Forward nur fuer 1 statt 8 Register:          7 Ops")
print("                                            ---------------")
print("                                                     52 Ops")
print()
print("  Zusammen mit der Vorwaerts-Spezialisierung (24 Ops):")
print("     880 - 24 - 52 = 804 Ops   ->  Ersparnis 8.6 %")
print()

# ---------- Wie weit traegt der Early-Exit statistisch? ----------
print("="*72)
print("EARLY-EXIT: der eigentliche Hebel")
print("="*72)
print("  Ist H_7 != 0, ist der Hash sicher zu gross -> Abbruch nach Runde 60.")
print("  Wahrscheinlichkeit, dass H_7 == 0 (32 Nullbits):  2^-32")
print("  D.h. in 4.294.967.295 von 4.294.967.296 Faellen bricht man")
print("  nach Runde 61 statt 64 ab.\n")
mittel = (61/64)*(1-2**-32) + 1*(2**-32)
print(f"  Mittlere Rundenzahl pro Hash: {mittel*64:.4f} statt 64")
print(f"  Ersparnis durch Early-Exit:   {(1-mittel)*100:.2f} %")
print()
print("  Kombiniert mit allem Vorherigen:")
gesamt = (1-mittel) + 0.027
print(f"    Vorwaerts-Spezialisierung : 2.7 %")
print(f"    Ausgangs-Kegel + Early-Exit: {(1-mittel)*100:.2f} %")
print(f"    GESAMT                     : ca. {gesamt*100:.1f} %")
print()
print("="*72)
print("WO DIE KUERZUNG ENDET - und warum")
print("="*72)
print("  Alles bisher Gekuerzte war: (a) Konstanten falten, (b) toter Code.")
print("  Beides sind SEMANTIKERHALTENDE Umformungen - sie aendern nichts an")
print("  der Funktion, nur an ihrer Ausfuehrung.")
print()
print("  Weiter kuerzen hiesse, Operationen zu entfernen, die das ERGEBNIS")
print("  aendern. Das geht nur, wenn man ihren Effekt vorhersagen kann -")
print("  und genau das ist ab Runde 5 unmoeglich (Grad >= 4, gemessen).")
print()
print("  Die 8.6 % sind damit nicht 'noch nicht genug optimiert',")
print("  sondern das VOLLSTAENDIGE Ergebnis der Konstantenpropagation auf K1.")
print("  Jede weitere Kuerzung muesste Nichtlinearitaet umgehen, nicht falten.")
