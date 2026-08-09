"""Waere ein K2 (nur EIN Ausgabebit) qualitativ einfacher?
Gemessen: Abhaengigkeitskegel und AND-Zahl pro Bit.
"""
import math
MASK=0xFFFFFFFF

class XAIG:
    def __init__(self):
        self.k=[('c0',)]; self.h={}
    def pi(self,n):
        self.k.append(('pi',n)); return 2*(len(self.k)-1)
    def _neu(self,t,a,b):
        if a>b: a,b=b,a
        key=(t,a,b)
        if key in self.h: return self.h[key]
        self.k.append((t,a,b)); l=2*(len(self.k)-1); self.h[key]=l; return l
    def UND(self,a,b):
        if a==0 or b==0: return 0
        if a==1: return b
        if b==1: return a
        if a==b: return a
        if a==(b^1): return 0
        return self._neu('and',a,b)
    def XOR(self,a,b):
        if a==0: return b
        if b==0: return a
        if a==1: return b^1
        if b==1: return a^1
        if a==b: return 0
        if a==(b^1): return 1
        return self._neu('xor',a&~1,b&~1)^((a&1)^(b&1))
    def ODER(self,a,b): return self.UND(a^1,b^1)^1
    def kegel(self,lits):
        ges=set(); st=[l>>1 for l in lits]
        while st:
            n=st.pop()
            if n in ges: continue
            ges.add(n); kn=self.k[n]
            if kn[0] in ('and','xor'): st+=[kn[1]>>1,kn[2]>>1]
        a=sum(1 for n in ges if self.k[n][0]=='and')
        x=sum(1 for n in ges if self.k[n][0]=='xor')
        pi=sum(1 for n in ges if self.k[n][0]=='pi')
        return a,x,pi

def wc(g,v): return [1 if (v>>i)&1 else 0 for i in range(32)]
def wpi(g,nm): return [g.pi(f"{nm}{i}") for i in range(32)]
def rotr(w,n): return [w[(i+n)%32] for i in range(32)]
def shr(w,n): return [w[i+n] if i+n<32 else 0 for i in range(32)]
def xw(g,a,b): return [g.XOR(x,y) for x,y in zip(a,b)]
def add(g,a,b):
    r=[];c=0
    for i in range(32):
        s=g.XOR(g.XOR(a[i],b[i]),c)
        c=g.ODER(g.UND(a[i],b[i]),g.UND(g.XOR(a[i],b[i]),c))
        r.append(s)
    return r
def ch(g,e,f,gg): return [g.XOR(gg[i],g.UND(e[i],g.XOR(f[i],gg[i]))) for i in range(32)]
def maj(g,a,b,c): return [g.XOR(g.UND(a[i],b[i]),g.UND(c[i],g.XOR(a[i],b[i]))) for i in range(32)]
def S0(g,x): return xw(g,xw(g,rotr(x,2),rotr(x,13)),rotr(x,22))
def S1(g,x): return xw(g,xw(g,rotr(x,6),rotr(x,11)),rotr(x,25))
def s0(g,x): return xw(g,xw(g,rotr(x,7),rotr(x,18)),shr(x,3))
def s1(g,x): return xw(g,xw(g,rotr(x,17),rotr(x,19)),shr(x,10))
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
PADv=[0x80000000,0,0,0,0,0,0,0x00000100]

def baue(runden):
    g=XAIG()
    W=[wpi(g,f"W{i}_") for i in range(8)]+[wc(g,v) for v in PADv]
    for t in range(16,runden):
        W.append(add(g,add(g,s1(g,W[t-2]),W[t-7]),add(g,s0(g,W[t-15]),W[t-16])))
    a,b,c,d,e,f,gg,h=[wc(g,v) for v in IVv]
    for t in range(runden):
        T1=add(g,add(g,add(g,h,S1(g,e)),ch(g,e,f,gg)),add(g,wc(g,K[t]),W[t]))
        T2=add(g,S0(g,a),maj(g,a,b,c))
        h,gg,f=gg,f,e
        e=add(g,d,T1); d,c,b=c,b,a; a=add(g,T1,T2)
    zust=[a,b,c,d,e,f,gg,h]
    aus=[add(g,wc(g,IVv[i]),zust[i]) for i in range(8)]
    return g,aus

print("="*80)
print("WIE GROSS IST DER KEGEL EINES EINZELNEN AUSGABEBITS?")
print("="*80)
print("  Verglichen: 1 Bit  vs.  1 Wort (32 Bit)  vs.  voller Zustand (256 Bit)\n")
for runden in [8,16,32,64]:
    g,aus=baue(runden)
    a_all,_,_ = g.kegel([b for w in aus for b in w])
    a_wort,_,_ = g.kegel(aus[7])
    # Bit 0 (niederwertigstes) und Bit 31 (hoechstwertiges) des letzten Wortes
    a_lsb,_,pi_lsb = g.kegel([aus[7][0]])
    a_msb,_,pi_msb = g.kegel([aus[7][31]])
    print(f"  --- {runden} Runden ---")
    print(f"    voller Zustand (256 Bit): {a_all:>8} AND")
    print(f"    ein Wort (32 Bit):        {a_wort:>8} AND   ({a_wort/a_all:>5.1%} davon)")
    print(f"    Bit 0  (niederwertigstes):{a_lsb:>8} AND   ({a_lsb/a_all:>5.1%}), "
          f"{pi_lsb} Eingaenge")
    print(f"    Bit 31 (hoechstwertiges): {a_msb:>8} AND   ({a_msb/a_all:>5.1%}), "
          f"{pi_msb} Eingaenge")
print()

print("="*80)
print("KEGELGROESSE ALLER 32 BITPOSITIONEN (64 Runden)")
print("="*80)
g,aus=baue(64)
a_all,_,_=g.kegel([b for w in aus for b in w])
print(f"  {'Bit':>4} {'AND-Gatter':>12} {'Anteil':>9} {'Eingaenge':>11}")
for bit in [0,1,2,4,8,16,24,31]:
    a,x,pi=g.kegel([aus[7][bit]])
    print(f"  {bit:>4} {a:>12} {a/a_all:>8.1%} {pi:>11}")
print()

print("="*80)
print("ANTWORT AUF DIE K2-FRAGE")
print("="*80)
g,aus=baue(64)
a_all,_,_=g.kegel([b for w in aus for b in w])
a_bit0,_,pi0=g.kegel([aus[7][0]])
print(f"  Ein einzelnes Ausgabebit haengt von {pi0} der 256 Eingabebits ab.")
print(f"  Sein Kegel umfasst {a_bit0:,} von {a_all:,} AND-Gattern "
      f"({a_bit0/a_all:.1%}).")
print()
print("  ZUM VERGLEICH die Reduktion, die wir bereits kennen:")
print("    volle Berechnung -> nur H_7:       9,6 % gespart (Abschnitt 3)")
print("    AIG -> XAIG:                      50,1 % gespart (Abschnitt 9.1)")
print(f"    volles Wort -> ein Bit:           {(1-a_bit0/a_all)*100:.1f} % gespart")
print()
print("  ENTSCHEIDEND ist aber nicht die Gatterzahl, sondern der SUCHRAUM.")
print(f"  Ein einzelnes Bit vorherzusagen bedeutet: 1 Bit Information.")
print(f"  Die Zufallstrefferquote ist 50 %. Um daraus einen Angriff zu bauen,")
print("  braeuchte man einen systematischen Vorteil - und den haben wir")
print("  heute mit sechs Methoden gesucht und nicht gefunden.")
print()
print("  DEIN EINWAND STIMMT: die Runden 62/63 schrumpfen den Kegel nur")
print("  am aeussersten Rand. Ab etwa 5 Runden rueckwaerts ist wieder")
print("  der volle Zustand noetig - das ist Satz 8 (Kegeltiefe 5).")
print("  Ein K2 waere quantitativ kleiner, qualitativ aber dasselbe Problem.")
