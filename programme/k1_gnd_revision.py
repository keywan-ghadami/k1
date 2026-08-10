"""Revision der Messmethodik zu Abschnitt 20 (Fortschrittskurve g(r)) und
Abschnitt 21 (neutrale Bits bei r = 17).

Anlass: die Kurve g(r) = 32(r-15) hat bei r = 17 einen Sprung von 0 auf 64,
also den doppelten Betrag der danach gemessenen Rate von 32 Bit je Runde.
Abschnitt 21 wollte klaeren, ob das ein Artefakt einer zu gross geratenen
Ratemenge ist, und hat die Frage mit einem Neutralitaetstest (Einzelbit-Flip)
verneint. Dieses Skript prueft die Methodik dieser beiden Messungen nach.

Fuenf Messungen, jede mit eigener Kontrolle:

  A  Seed-Stabilitaet der publizierten Kurve. Abschnitt 20.3 nennt nur einen
     Lauf (seed = 0). Reproduziert die Kurve ueber mehrere Instanzen?

  B  Trennschaerfe des Flip-Tests aus 21.2. Der Test wird zusaetzlich auf eine
     nachweislich VIEL ZU GROSSE Ratemenge angewandt (ebenenweise Rateordnung,
     250 statt 64 Bit). Meldet er auch dort null neutrale Bits, kann er eine
     ueberdimensionierte Menge grundsaetzlich nicht erkennen - dann traegt er
     die Schlussfolgerung aus 21.4 nicht.

  C  Der Test, der die Frage aus 21 tatsaechlich beantwortet: leave-one-out.
     Nicht "Bit i kippen", sondern "Bit i WEGLASSEN" - schliesst die Propagation
     auch ohne dieses Bit? Nur das misst Notwendigkeit.

  D  Aufhebung der stillschweigenden Beschraenkung auf Nachrichtenbits.
     g(r) wurde ausschliesslich ueber W0..W7 gemessen. Guess-and-Determine darf
     aber jede Variable raten. Gemessen wird hier die Ratemenge ueber den
     Expansionswoertern W16..W(r-1), mit Korrektheitsprobe (rekonstruierte
     Nachricht bitidentisch, Nachrechnung trifft den Zielhash).

  E  Substanz der Positivkontrolle aus 21.3. Instrumentiert, wie viele
     Propagationsschritte die Kontrolle ueberhaupt ausloest.

Nutzt ausschliesslich die vorhandene Propagationsmaschine (k1_propagation.py)
und die vorhandene Kodierung (k1_cnf.py). Kein externer Solver.
"""
import random, sys
sys.path.insert(0, ".")
from k1_cnf import baue, sha_ref, PAD
from k1_propagation import Prop

M32 = 0xFFFFFFFF


def instanz(r, seed=0):
    rng = random.Random(seed)
    W16 = [rng.getrandbits(32) for _ in range(8)] + PAD
    ziel = sha_ref(W16, r)
    F, frei, H, W = baue(r, "k1", W16, ziel, mit_W=True)
    return F, frei, W, W16, ziel


def frisch(F):
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    return p


def rate(p, F, lits):
    """Literale der Reihe nach auf ihren Loesungswert setzen, bereits
    bestimmte ueberspringen. Rueckgabe: (Zahl der geratenen, Rest offen)."""
    g = 0
    for l in lits:
        if p.val(l) >= 0: continue
        g += 1
        if not p.entschieden(l if F.lv(l) else -l):
            return None, None
    return g, p.offen()


ORD_WORT  = list(range(256))                                    # W0.b0..W7.b31
ORD_EBENE = [w*32 + b for b in range(32) for w in range(8)]      # Bitebenen


# ===================================================== A  Seed-Stabilitaet
print("=" * 76)
print("A  IST DIE KURVE AUS 20.3 UEBER INSTANZEN STABIL?")
print("=" * 76)
print("   (das Dokument nennt nur seed = 0)")
print(f"  {'r':>3} " + " ".join(f"{'seed '+str(s):>8}" for s in range(5)) + f" {'Soll 32(r-15)':>14}")
for r in (16, 17, 18, 19, 20, 21, 22):
    zeile = []
    for s in range(5):
        F, frei, W, _, _ = instanz(r, s)
        g, off = rate(frisch(F), F, [frei[k] for k in ORD_WORT])
        zeile.append(f"{g}" if off == 0 else f"{g}/off{off}")
    soll = 32 * (r - 15) if r >= 17 else 0   # 20.3 gilt fuer 17 <= r <= 23
    print(f"  {r:>3} " + " ".join(f"{z:>8}" for z in zeile) + f" {soll:>14}")
print("  -> Befund: die Kurve selbst ist reproduzierbar. Der Verdacht muss")
print("     also der Definition der Messgroesse gelten, nicht der Streuung.")


# ===================================================== B  Trennschaerfe Flip
print()
print("=" * 76)
print("B  KANN DER FLIP-TEST AUS 21.2 EINE ZU GROSSE RATEMENGE ERKENNEN?")
print("=" * 76)

def ratemenge(F, frei, ordnung):
    p = frisch(F)
    ger = []
    for k in ordnung:
        l = frei[k]
        if p.val(l) >= 0: continue
        ger.append(k)
        assert p.entschieden(l if F.lv(l) else -l), "unerwarteter Konflikt"
    assert p.offen() == 0, "Ratemenge schliesst das System nicht"
    return ger

def flip_test(F, frei, ger):
    """Wortgleich die Logik aus k1_neutral_bits.neutral_test."""
    basis = frisch(F)
    m0 = basis.mark()
    neutral = 0
    for k_flip in ger:
        konflikt = False
        for k in ger:
            l = frei[k]
            soll = F.lv(l) ^ (1 if k == k_flip else 0)
            lit = l if soll else -l
            v = basis.val(lit)
            if v == 1: continue
            if v == 0 or not basis.entschieden(lit):
                konflikt = True; break
        if (not konflikt) and basis.offen() == 0:
            neutral += 1
        basis.undo(m0)
    return neutral

R = 17
print(f"  {'seed':>4} {'|wortweise|':>12} {'|ebenenweise|':>14} "
      f"{'flip(wort)':>11} {'flip(ebene)':>12}")
for seed in (0, 1, 2):
    F, frei, W, _, _ = instanz(R, seed)
    gw = ratemenge(F, frei, ORD_WORT)
    ge = ratemenge(F, frei, ORD_EBENE)
    print(f"  {seed:>4} {len(gw):>12} {len(ge):>14} "
          f"{flip_test(F, frei, gw):>11} {flip_test(F, frei, ge):>12}")
print("  -> Die ebenenweise Menge ist um ~186 Bit zu gross; der Flip-Test meldet")
print("     auch dort null neutrale Bits. Er hat gegen Ueberdimensionierung")
print("     keine Trennschaerfe.")
print("  Grund: ist S ein starkes Backdoor bzgl. Unit-Propagation, so bestimmt")
print("  die Propagation aus JEDER Belegung von S alles Uebrige oder meldet")
print("  Konflikt. Ein geflipptes Bit kann daher nur dann 'neutral' heissen,")
print("  wenn ein ZWEITES Urbild mit genau dieser Belegung existiert -")
print("  Erwartungswert 2^-64 pro Flip. Null Treffer sind die Vorhersage des")
print("  Nullmodells, kein Strukturbefund.")


# ===================================================== C  leave-one-out
print()
print("=" * 76)
print("C  DER TEST, DER NOTWENDIGKEIT WIRKLICH MISST: LEAVE-ONE-OUT")
print("=" * 76)

def leave_one_out(F, frei, ger):
    ueberfluessig, offen = 0, []
    for k_weg in ger:
        p = frisch(F)
        for k in ger:
            if k == k_weg: continue
            l = frei[k]
            if p.val(l) >= 0: continue
            p.entschieden(l if F.lv(l) else -l)
        o = p.offen(); offen.append(o)
        if o == 0: ueberfluessig += 1
    return ueberfluessig, min(offen), max(offen)

print(f"  {'seed':>4} {'Menge':>12} {'Groesse':>8} {'entbehrlich':>12} {'Restoffenheit':>16}")
for seed in (0, 1):
    F, frei, W, _, _ = instanz(R, seed)
    for name, ordn in (("wortweise", ORD_WORT), ("ebenenweise", ORD_EBENE)):
        ger = ratemenge(F, frei, ordn)
        u, mn, mx = leave_one_out(F, frei, ger)
        print(f"  {seed:>4} {name:>12} {len(ger):>8} {u:>12} {str(mn)+'..'+str(mx):>16}")
print("  -> Leave-one-out erkennt die ueberdimensionierte Menge sofort und")
print("     bestaetigt die wortweise Menge als einzeln-minimal. Das ist die")
print("     Kontrolle, die 21.3 haette leisten muessen.")


# ===================================================== D  jenseits W0..W7
print()
print("=" * 76)
print("D  RATEMENGE OHNE BESCHRAENKUNG AUF NACHRICHTENBITS")
print("=" * 76)
print("   g(r) wurde nur ueber W0..W7 gemessen. Guess-and-Determine darf jede")
print("   Variable raten. Hier: die Expansionswoerter W16..W(r-1).")
print()
print(f"  {'r':>3} {'g ueber W0..W7':>15} {'g* ueber W16..':>15} {'Diff':>6} "
      f"{'Nachricht rekonstr.':>20} {'trifft Ziel':>12}")
for r in range(16, 25):
    F, frei, W, W16, ziel = instanz(r, 0)
    # beide Zahlen gemessen, keine aus der Formel eingesetzt
    gm, offm = rate(frisch(F), F, [frei[k] for k in ORD_WORT])
    gm = f"{gm}" if offm == 0 else f"{gm}/off{offm}"
    p = frisch(F)
    g, off = rate(p, F, [l for t in range(16, r) for l in W[t]])
    if off == 0:
        rek = [sum((1 if p.val(frei[w*32+b]) == 1 else 0) << b for b in range(32))
               for w in range(8)]
        stimmt = (rek == W16[:8])
        trifft = (sha_ref(rek + PAD, r) == ziel)
    else:
        stimmt = trifft = f"offen={off}"
    diff = (int(gm) - g) if gm.isdigit() else "—"
    print(f"  {r:>3} {gm:>15} {g:>15} {str(diff):>6} {str(stimmt):>20} {str(trifft):>12}")
print()
print("  -> g*(r) = 32 (r - 16), durchgehend 32 Bit unter der publizierten Kurve.")
print("     Der Sprung bei r = 17 betraegt damit 32, nicht 64: die glatte Rate")
print("     von 32 Bit je Runde gilt ab r = 16 ohne Ausnahme.")
print()
print("  Struktureller Grund (im Padding nachrechenbar): W9 = W14 = 0, also")
print("     W16 = s1(W14) + W9 + s0(W1) + W0 = W0 + s0(W1).")
ro = lambda x, n: ((x >> n) | (x << (32-n))) & M32
s0f = lambda x: ro(x,7) ^ ro(x,18) ^ (x >> 3)
s1f = lambda x: ro(x,17) ^ ro(x,19) ^ (x >> 10)
rng = random.Random(7)
proben = []
for _ in range(1000):
    Wv = [rng.getrandbits(32) for _ in range(8)] + PAD
    proben.append(((s1f(Wv[14]) + Wv[9] + s0f(Wv[1]) + Wv[0]) & M32)
                  == ((Wv[0] + s0f(Wv[1])) & M32))
print(f"     Nachgerechnet an 1000 Zufallsnachrichten: {all(proben)}")
print("  Die 17. Runde verbraucht also nur das 32-Bit-Aggregat W0 + s0(W1),")
print("  nicht die 64 Bit von W0 und W1 einzeln. Wer W0 und W1 raet, bezahlt")
print("  32 Bit fuer eine Information, die die Runde gar nicht anfordert.")
print()

def rang_gf2(f):
    B = [f(1 << i) for i in range(32)]
    r, piv = 0, []
    for b in range(32):
        for i, v in enumerate(B):
            if (v >> b) & 1 and i not in piv:
                piv.append(i); r += 1
                B = [x ^ v if (j != i and (x >> b) & 1) else x for j, x in enumerate(B)]
                break
    return r
print(f"  Erschoepfbarkeit der Aufzaehlung: Rang s0 = {rang_gf2(s0f)}, "
      f"Rang s1 = {rang_gf2(s1f)} ueber GF(2).")
print("  Beide sind bijektiv, und W(16+j) enthaelt Wj additiv. Die Abbildung")
print("  (W0..W7) -> (W16..W23) ist damit dreiecksfoermig bijektiv: der Raum")
print("  der aufzuzaehlenden Expansionswoerter ist vollstaendig erreichbar,")
print("  2^g* ist keine ueberzaehlende Schranke.")


# ===================================================== E  Positivkontrolle
print()
print("=" * 76)
print("E  WIE VIEL PRUEFT DIE POSITIVKONTROLLE AUS 21.3?")
print("=" * 76)
F, frei, W, _, _ = instanz(R, 0)
p = frisch(F)
ger = []
for k in ORD_WORT:
    l = frei[k]
    if p.val(l) >= 0: continue
    ger.append(k); p.entschieden(l if F.lv(l) else -l)
m = p.mark()
print(f"  nach vollstaendigem Raten: offen = {p.offen()} (alles bestimmt)")
ausserhalb = [k for k in range(256) if k not in set(ger)]
schritte = []
for k in random.Random(1000).sample(ausserhalb, 20):
    l = frei[k]
    lit = -l if F.lv(l) else l
    vor = len(p.trail)
    p.entschieden(lit)
    schritte.append(len(p.trail) - vor)
    p.undo(m)
print(f"  Trail-Zuwachs je geflipptem Bit: {sorted(set(schritte))}, "
      f"Summe {sum(schritte)}")
print("  -> Die Kontrolle loest KEINEN einzigen Propagationsschritt aus. Der")
print("     Konflikt entsteht bereits in enqueue(), weil die Variable schon")
print("     belegt ist. Geprueft wird damit nur, dass val() eine belegte")
print("     Variable erkennt - nicht mark/undo, nicht die Propagation. Als")
print("     Absicherung des Nullbefunds aus 21.2 taugt sie nicht.")
