"""Andere Verdrahtung, identisches Ergebnis.
SHA-256 als ZWEI gekoppelte Rekursionen statt acht Registern.
"""
import struct, hashlib, random, math
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
K=[icbrt(p*(1<<96))&MASK for p in primes(64)]
IV=[math.isqrt(p*(1<<64))&MASK for p in primes(8)]

# ================= FORM A: Standard, 8 Register =================
def form_A(W):
    a,b,c,d,e,f,g,h = IV
    for t in range(64):
        T1=(h+S1(e)+Ch(e,f,g)+K[t]+W[t])&MASK
        T2=(S0(a)+Maj(a,b,c))&MASK
        h,g,f = g,f,e
        e=(d+T1)&MASK
        d,c,b = c,b,a
        a=(T1+T2)&MASK
    return tuple((x+y)&MASK for x,y in zip(IV,(a,b,c,d,e,f,g,h)))

# ================= FORM B: zwei Rekursionen, KEINE b,c,d,f,g,h =================
# Herleitung:  b_t = a_{t-1},  c_t = a_{t-2},  d_t = a_{t-3}
#              f_t = e_{t-1},  g_t = e_{t-2},  h_t = e_{t-3}
# also:
#   T1_t = e_{t-4} + Sigma1(e_{t-1}) + Ch(e_{t-1}, e_{t-2}, e_{t-3}) + K_t + W_t
#   T2_t = Sigma0(a_{t-1}) + Maj(a_{t-1}, a_{t-2}, a_{t-3})
#   e_t  = a_{t-4} + T1_t
#   a_t  = T1_t + T2_t
def form_B(W):
    # Historie: Index 0 = juengster Wert. Startbelegung aus dem IV.
    A=[IV[0], IV[1], IV[2], IV[3]]      # a_{-1}, a_{-2}, a_{-3}, a_{-4}
    E=[IV[4], IV[5], IV[6], IV[7]]      # e_{-1}, e_{-2}, e_{-3}, e_{-4}
    for t in range(64):
        T1=(E[3] + S1(E[0]) + Ch(E[0],E[1],E[2]) + K[t] + W[t])&MASK
        T2=(S0(A[0]) + Maj(A[0],A[1],A[2]))&MASK
        e_neu=(A[3]+T1)&MASK
        a_neu=(T1+T2)&MASK
        A=[a_neu]+A[:3]
        E=[e_neu]+E[:3]
    zustand=(A[0],A[1],A[2],A[3],E[0],E[1],E[2],E[3])
    return tuple((x+y)&MASK for x,y in zip(IV,zustand))

# ================= FORM C: zwei Runden zusammengefasst =================
# Runde t und t+1 in einem Schritt, ohne Zwischenzustand zu materialisieren
def form_C(W):
    A=[IV[0], IV[1], IV[2], IV[3]]
    E=[IV[4], IV[5], IV[6], IV[7]]
    for t in range(0,64,2):
        # --- Schritt t ---
        T1a=(E[3] + S1(E[0]) + Ch(E[0],E[1],E[2]) + K[t] + W[t])&MASK
        T2a=(S0(A[0]) + Maj(A[0],A[1],A[2]))&MASK
        e1=(A[3]+T1a)&MASK
        a1=(T1a+T2a)&MASK
        # --- Schritt t+1, direkt mit den neuen Werten ---
        T1b=(E[2] + S1(e1) + Ch(e1,E[0],E[1]) + K[t+1] + W[t+1])&MASK
        T2b=(S0(a1) + Maj(a1,A[0],A[1]))&MASK
        e2=(A[2]+T1b)&MASK
        a2=(T1b+T2b)&MASK
        A=[a2,a1,A[0],A[1]]
        E=[e2,e1,E[0],E[1]]
    zustand=(A[0],A[1],A[2],A[3],E[0],E[1],E[2],E[3])
    return tuple((x+y)&MASK for x,y in zip(IV,zustand))

def schedule(msg64):
    W=list(struct.unpack('>16I',msg64))
    for t in range(16,64):
        W.append((s1(W[t-2])+W[t-7]+s0(W[t-15])+W[t-16])&MASK)
    return W

print("="*76)
print("VERIFIKATION: drei verschiedene Verdrahtungen, gleiches Ergebnis?")
print("="*76)
rng=random.Random(2026)
ok_AB=ok_AC=True
for _ in range(3000):
    m=bytes(rng.randrange(256) for _ in range(64))
    W=schedule(m)
    a=form_A(W); b=form_B(W); c=form_C(W)
    ok_AB &= (a==b); ok_AC &= (a==c)
print(f"  Form A (Standard, 8 Register) == Form B (2 Rekursionen):  {ok_AB}")
print(f"  Form A == Form C (2 Runden zusammengefasst):              {ok_AC}")

# Gegen hashlib
def sha256_via(form):
    msg=b'abc'
    padded=msg+b'\x80'+b'\x00'*52+struct.pack('>Q',24)
    H=form(schedule(padded))
    return b''.join(struct.pack('>I',x) for x in H)
print(f"\n  Form B gegen hashlib('abc'): {sha256_via(form_B)==hashlib.sha256(b'abc').digest()}")
print(f"  Form C gegen hashlib('abc'): {sha256_via(form_C)==hashlib.sha256(b'abc').digest()}")

print()
print("="*76)
print("WAS SICH AN DER VERDRAHTUNG AENDERT")
print("="*76)
print("  FORM A (Standard):")
print("    8 Register a..h, pro Runde 6 Kopieroperationen (h<-g, g<-f, f<-e,")
print("    d<-c, c<-b, b<-a) plus 2 Neuberechnungen.")
print()
print("  FORM B (zwei Rekursionen):")
print("    Nur noch a und e existieren als Groessen. Die uebrigen sechs Register")
print("    sind ZEITVERSCHOBENE Werte derselben zwei Ketten:")
print("      b_t = a_{t-1}   c_t = a_{t-2}   d_t = a_{t-3}")
print("      f_t = e_{t-1}   g_t = e_{t-2}   h_t = e_{t-3}")
print("    Damit lautet die Runde:")
print("      T1 = e_{t-4} + Sigma1(e_{t-1}) + Ch(e_{t-1},e_{t-2},e_{t-3}) + K + W")
print("      T2 = Sigma0(a_{t-1}) + Maj(a_{t-1},a_{t-2},a_{t-3})")
print("      e_t = a_{t-4} + T1")
print("      a_t = T1 + T2")
print()
print("    In Hardware: zwei 4-stufige Schieberegister statt acht Einzelregister.")
print("    Die 6 Kopieroperationen entfallen vollstaendig - sie sind Verdrahtung.")
print()
print("  FORM C (2 Runden gefusst):")
print("    Der Zwischenzustand nach Runde t wird nie materialisiert.")
print("    Halbiert die Zahl der Registerschreibvorgaenge.")

print()
print("="*76)
print("OPERATIONSBILANZ")
print("="*76)
zeilen=[("Register-Kopien pro Runde", 6, 0, "reine Verdrahtung in Form B"),
        ("Sigma-Aufrufe", 2, 2, ""),
        ("Ch/Maj", 2, 2, ""),
        ("modulare Additionen", 7, 7, "unveraendert"),
        ("Registerschreibvorgaenge", 8, 2, "nur a und e")]
sa=sb=0
print(f"  {'':<30} {'Form A':>8} {'Form B':>8}  Bemerkung")
for n,x,y,b in zeilen:
    sa+=x; sb+=y
    print(f"  {n:<30} {x:>8} {y:>8}  {b}")
print(f"  {'-'*66}")
print(f"  {'SUMME':<30} {sa:>8} {sb:>8}")
print()
print("  Die ARITHMETIK ist identisch - 7 Additionen bleiben 7 Additionen.")
print("  Was wegfaellt, sind Datenbewegungen: 6 Kopien und 6 Registerschreibungen")
print("  pro Runde. In Software spart das Register und Befehle, in Hardware")
print("  Flipflops und Multiplexer.")
print()
print("  DAS IST EINE ANDERE VERDRAHTUNG MIT IDENTISCHEM ERGEBNIS -")
print("  bewiesen an 3000 Zufallseingaben und gegen hashlib.")
