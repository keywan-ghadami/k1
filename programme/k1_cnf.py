"""Wiederverwendbarer Baustein: CNF-Kodierung der rundenreduzierten
SHA-256-Kompressionsfunktion. Enthaelt keine Messungen, nur die Konstruktion.
Ausfuehrliche Korrektheitsnachweise siehe k1_sat_kodierung.py.

Kodierungsvarianten (Abschnitt 9.1 / 22.4). Die Vorgabewerte reproduzieren
exakt das bisherige Verhalten, auf dem die Abschnitte 20 und 21 beruhen:

  xor_nativ=True        natives XOR-Gatter. False: ueber AND/NOT zerlegt.
  carry_variante="or"   Maj/Uebertrag als monolithisches Tseitin-Gatter
                        (bisheriges Verhalten; entspricht KEINER Zeile aus 9.1).
                 "or_gatter"    Maj/Uebertrag aus AND/OR/XOR aufgebaut, exakt
                                in den Formen aus auftrag_1_2.py (9.1-Zeilen
                                "AIG-Basis" bzw. "XAIG, OR-Uebertrag").
                 "and_minimal"  AND-minimaler Uebertrag (9.1-Zeile
                                "XAIG, AND-minimaler Uebertrag").
  hashing=False         kein Dedup. True: strukturelles Hashing wie im XAIG
                        aus auftrag_1_2.py - noetig, damit die Gatterzahlen
                        mit 9.1 vergleichbar sind.
  assoz="linear"        Additionsketten links-linear (bisheriges Verhalten).
                 "baum" Klammerung exakt wie in auftrag_1_2.py, noetig fuer
                        den Zahlenvergleich mit 9.1.
"""
M32 = 0xFFFFFFFF

def frac(x, n=32): return int((x - int(x)) * (1 << n))
def primes(k):
    ps, c = [], 2
    while len(ps) < k:
        if all(c % p for p in ps if p*p <= c): ps.append(c)
        c += 1
    return ps
P   = primes(64)
IV  = [frac(p**0.5) for p in P[:8]]
K   = [frac(p**(1/3.)) for p in P]
PAD = [0x80000000, 0, 0, 0, 0, 0, 0, 0x00000100]


class CNF:
    def __init__(self, xor_nativ=True, carry_variante="or",
                 hashing=False, assoz="linear"):
        self.xor_nativ = xor_nativ
        self.carry_variante = carry_variante
        self.hashing = hashing
        self.assoz = assoz
        self.cache = {}
        self.stat = {"and": 0, "xor": 0, "maj": 0}
        self.n = 0; self.cls = []; self.val = {}
        self.TRUE = self.newvar(1); self.cls.append([self.TRUE])
    def newvar(self, v):
        self.n += 1; self.val[self.n] = v & 1; return self.n
    def add(self, *l): self.cls.append(list(l))
    def lv(self, l): return self.val[abs(l)] ^ (1 if l < 0 else 0)
    def const(self, b): return self.TRUE if b else -self.TRUE
    def is_const(self, l):
        if l == self.TRUE: return 1
        if l == -self.TRUE: return 0
        return None

    # ------------------------------------------------------------ Gatter
    def XOR(self, a, b):
        ca, cb = self.is_const(a), self.is_const(b)
        if ca is not None: return b if ca == 0 else -b
        if cb is not None: return a if cb == 0 else -a
        if a == b: return self.const(0)
        if a == -b: return self.const(1)
        if not self.xor_nativ:
            # AIG-Basis: kein XOR-Knoten, drei AND-Aequivalente
            return self.OR(self.AND(a, -b), self.AND(-a, b))
        key = par = None
        if self.hashing:
            va, vb = abs(a), abs(b)
            par = (1 if a < 0 else 0) ^ (1 if b < 0 else 0)
            key = ("xor", min(va, vb), max(va, vb))
            if key in self.cache:
                s = self.cache[key]
                return -s if par else s
        c = self.newvar(self.lv(a) ^ self.lv(b)); self.stat["xor"] += 1
        self.add(a, b, -c); self.add(a, -b, c)
        self.add(-a, b, c); self.add(-a, -b, -c)
        if self.hashing: self.cache[key] = -c if par else c
        return c

    def AND(self, a, b):
        ca, cb = self.is_const(a), self.is_const(b)
        if ca is not None: return self.const(0) if ca == 0 else b
        if cb is not None: return self.const(0) if cb == 0 else a
        if a == b: return a
        if a == -b: return self.const(0)
        key = None
        if self.hashing:
            key = ("and", min(a, b), max(a, b))
            if key in self.cache: return self.cache[key]
        c = self.newvar(self.lv(a) & self.lv(b)); self.stat["and"] += 1
        self.add(-a, -b, c); self.add(a, -c); self.add(b, -c)
        if self.hashing: self.cache[key] = c
        return c

    def OR(self, a, b): return -self.AND(-a, -b)

    def MAJ(self, a, b, c):
        for x, y, z in ((a,b,c), (b,a,c), (c,a,b)):
            k = self.is_const(x)
            if k is not None: return self.OR(y,z) if k == 1 else self.AND(y,z)
        if self.carry_variante == "and_minimal":
            # maj_MIN aus auftrag_1_2.py: ((a^b)&(b^c))^b - ein AND
            return self.XOR(self.AND(self.XOR(a,b), self.XOR(b,c)), b)
        if self.carry_variante == "or_gatter":
            # maj_OR aus auftrag_1_2.py: (a&b) ^ (c&(a^b))
            return self.XOR(self.AND(a,b), self.AND(c, self.XOR(a,b)))
        key = None
        if self.hashing:
            key = ("maj",) + tuple(sorted((a,b,c)))
            if key in self.cache: return self.cache[key]
        m = self.newvar((self.lv(a)&self.lv(b)) ^ (self.lv(a)&self.lv(c)) ^ (self.lv(b)&self.lv(c)))
        self.stat["maj"] += 1
        self.add(-a,-b,m); self.add(-a,-c,m); self.add(-b,-c,m)
        self.add(a,b,-m); self.add(a,c,-m); self.add(b,c,-m)
        if self.hashing: self.cache[key] = m
        return m

    def CH(self, e, f, g): return self.XOR(g, self.AND(e, self.XOR(f, g)))

    # ------------------------------------------------------------ Wortebene
    def wconst(self, v): return [self.const((v >> i) & 1) for i in range(32)]
    def wvar(self, v):   return [self.newvar((v >> i) & 1) for i in range(32)]
    def wval(self, w):   return sum(self.lv(l) << i for i, l in enumerate(w))
    def rotr(self, w, k): return [w[(i+k) % 32] for i in range(32)]
    def shr(self, w, k):  return [w[i+k] if i+k < 32 else self.const(0) for i in range(32)]
    def wxor(self, *ws):
        r = ws[0]
        for w in ws[1:]: r = [self.XOR(x,y) for x,y in zip(r,w)]
        return r

    def add32(self, x, y):
        """Ripple-Carry. Die Uebertragsform folgt carry_variante und ist fuer
        'or_gatter'/'and_minimal' strukturgleich mit add_OR/add_MIN aus
        auftrag_1_2.py (gleiche Teilausdruecke, damit gleiche Knotenzahl)."""
        out, c = [], self.const(0)
        for i in range(32):
            if self.carry_variante == "and_minimal":
                ac = self.XOR(x[i], c); bc = self.XOR(y[i], c)
                out.append(self.XOR(ac, y[i]))
                if i < 31: c = self.XOR(self.AND(ac, bc), c)
            elif self.carry_variante == "or_gatter":
                xy = self.XOR(x[i], y[i])
                out.append(self.XOR(xy, c))
                if i < 31: c = self.OR(self.AND(x[i], y[i]), self.AND(xy, c))
            else:
                out.append(self.XOR(self.XOR(x[i], y[i]), c))
                if i < 31: c = self.MAJ(x[i], y[i], c)
        return out

    def addn(self, *ws):
        r = ws[0]
        for w in ws[1:]: r = self.add32(r, w)
        return r


def sha_ref(W16, r):
    ro = lambda x,n: ((x>>n)|(x<<(32-n))) & M32
    s0 = lambda x: ro(x,7)^ro(x,18)^(x>>3)
    s1 = lambda x: ro(x,17)^ro(x,19)^(x>>10)
    W = list(W16)
    for t in range(16, r): W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16]) & M32)
    a,b,c,d,e,f,g,h = IV
    for t in range(r):
        T1 = (h + (ro(e,6)^ro(e,11)^ro(e,25)) + ((e&f)^(~e&g&M32)) + K[t] + W[t]) & M32
        T2 = ((ro(a,2)^ro(a,13)^ro(a,22)) + ((a&b)^(a&c)^(b&c))) & M32
        h,g,f,e,d,c,b,a = g,f,e,(d+T1)&M32,c,b,a,(T1+T2)&M32
    return [(x+y) & M32 for x,y in zip([a,b,c,d,e,f,g,h], IV)]


def baue(r, modus, W16_ref, ziel, xor_nativ=True, carry_variante="or",
         hashing=False, assoz="linear", mit_W=False):
    """CNF fuer: r-rundige Kompression einer Nachricht == ziel.
    modus 'block' = 512 freie Bits, 'k1' = 256 freie Bits mit festem Padding.
    Kodierungsvarianten siehe CNF.
    Rueckgabe: (CNF, freie Literale in Reihenfolge W0.bit0 .. W7.bit31, H).
    Mit mit_W=True zusaetzlich die Wortliste W (auch die Expansionswoerter
    W16..W(r-1)) als viertes Element - noetig, um Ratemengen zu untersuchen,
    die nicht auf Nachrichtenbits beschraenkt sind (Abschnitt 24)."""
    F = CNF(xor_nativ=xor_nativ, carry_variante=carry_variante,
            hashing=hashing, assoz=assoz)
    baum = (assoz == "baum")
    if modus == "block":
        W = [F.wvar(W16_ref[i]) for i in range(16)]
        frei = [l for w in W for l in w]
    else:
        W = [F.wvar(W16_ref[i]) for i in range(8)] + [F.wconst(v) for v in PAD]
        frei = [l for w in W[:8] for l in w]
    for t in range(16, r):
        s0 = F.wxor(F.rotr(W[t-15],7), F.rotr(W[t-15],18), F.shr(W[t-15],3))
        s1 = F.wxor(F.rotr(W[t-2],17), F.rotr(W[t-2],19), F.shr(W[t-2],10))
        if baum:
            W.append(F.add32(F.add32(s1, W[t-7]), F.add32(s0, W[t-16])))
        else:
            W.append(F.addn(s1, W[t-7], s0, W[t-16]))
    st = [F.wconst(v) for v in IV]
    for t in range(r):
        a,b,c,d,e,f,g,h = st
        S1 = F.wxor(F.rotr(e,6), F.rotr(e,11), F.rotr(e,25))
        S0 = F.wxor(F.rotr(a,2), F.rotr(a,13), F.rotr(a,22))
        ch = [F.CH(e[i],f[i],g[i]) for i in range(32)]
        mj = [F.MAJ(a[i],b[i],c[i]) for i in range(32)]
        if baum:
            T1 = F.add32(F.add32(F.add32(h, S1), ch), F.add32(F.wconst(K[t]), W[t]))
        else:
            T1 = F.addn(h, S1, ch, F.wconst(K[t]), W[t])
        T2 = F.add32(S0, mj)
        st = [F.add32(T1,T2), a, b, c, F.add32(d,T1), e, f, g]
    if baum:
        H = [F.add32(F.wconst(IV[i]), st[i]) for i in range(8)]
    else:
        H = [F.add32(st[i], F.wconst(IV[i])) for i in range(8)]
    for i in range(8):
        for j in range(32):
            F.add(H[i][j] if (ziel[i] >> j) & 1 else -H[i][j])
    return (F, frei, H, W) if mit_W else (F, frei, H)
