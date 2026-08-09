"""Fortsetzung von Abschnitt 21: gemeinsame Neutralitaet von Bitpaaren bei
r = 17.

Abschnitt 21 (k1_neutral_bits.py) zeigt: einzeln ist keines der 64 wortweise
geratenen Nachrichtenbits neutral (Satz K). Offen blieb dort ausdruecklich
die naechste Stufe (21.4, "Reichweite der Aussage"): ob ein PAAR von Bits
gemeinsam geflippt werden kann, obwohl keines der beiden einzeln neutral
ist - ein Fall, den der Einzelbit-Test nicht erfasst.

Definition (Erweiterung von Abschnitt 21.1 auf zwei Bits):

  Ein Paar geratener Bits (i, j) ist GEMEINSAM NEUTRAL, wenn die Propagation
  bei allen uebrigen 62 geratenen Bits auf ihrem Loesungswert und i UND j
  gleichzeitig auf dem GEFLIPPTEN Wert konfliktfrei alle Variablen bestimmt.

Bei 64 geratenen Bits gibt es C(64,2) = 2016 Paare je Instanz. Gemessen an
denselben zehn Zufallsinstanzen wie in Abschnitt 21, mit derselben
Propagationsmaschine (k1_propagation.py), kein externer Solver.

Kontrolle: dieselbe Positivkontrolle wie in 21.3 gilt unveraendert weiter
(sie prueft die Testmaschinerie, nicht die Ratemenge) und wird hier nicht
wiederholt.
"""
import random, sys, time
sys.path.insert(0, ".")
from k1_cnf import baue, sha_ref, PAD
from k1_propagation import Prop

R = 17
SEEDS = 10


def instanz(seed):
    rng = random.Random(seed)
    W16 = [rng.getrandbits(32) for _ in range(8)] + PAD
    ziel = sha_ref(W16, R)
    F, frei, H = baue(R, "k1", W16, ziel)
    return F, frei


def wortweise_ratemenge(F, frei):
    """Wie in k1_neutral_bits.py: liefert die frei-Indizes, die tatsaechlich
    geraten werden muessen, in Ratereihenfolge."""
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    geraten = []
    for k in range(len(frei)):
        l = frei[k]
        if p.val(l) >= 0:
            continue
        geraten.append(k)
        lit = l if F.lv(l) else -l
        ok = p.entschieden(lit)
        assert ok, "Konflikt beim Aufbau der Referenzloesung - unerwartet"
    assert p.offen() == 0, f"wortweises Raten schliesst r={R} nicht vollstaendig"
    return geraten


def neutral_paar_test(F, frei, geraten):
    """Fuer jedes der C(64,2) Bitpaare: bleibt die Propagation bei allen
    uebrigen 62 Bits auf Loesungswert und diesem Paar gleichzeitig geflippt
    konfliktfrei und vollstaendig? -> Paar ist gemeinsam neutral."""
    basis = Prop([list(c) for c in F.cls], F.n)
    basis.start()
    m0 = basis.mark()
    n = len(geraten)
    treffer = []
    geprueft = 0
    for a in range(n):
        ka = geraten[a]
        for b in range(a + 1, n):
            kb = geraten[b]
            konflikt = False
            for k in geraten:
                l = frei[k]
                soll = F.lv(l)
                if k == ka or k == kb:
                    soll ^= 1
                lit = l if soll else -l
                v = basis.val(lit)
                if v == 1:
                    continue
                if v == 0:
                    konflikt = True
                    break
                if not basis.entschieden(lit):
                    konflikt = True
                    break
            geprueft += 1
            if (not konflikt) and basis.offen() == 0:
                treffer.append((ka, kb))
            basis.undo(m0)
    return treffer, geprueft


if __name__ == "__main__":
    print("=" * 76)
    print(f"GEMEINSAME NEUTRALITAET VON BITPAAREN BEI r = {R}")
    print("=" * 76)
    print(f"  {'seed':>4} {'g(r)':>5} {'Paare':>7} {'neutral':>8}  Zeit (s)")

    alle_treffer = []
    t_start = time.time()
    for seed in range(SEEDS):
        t0 = time.time()
        F, frei = instanz(seed)
        geraten = wortweise_ratemenge(F, frei)
        treffer, geprueft = neutral_paar_test(F, frei, geraten)
        dt = time.time() - t0
        alle_treffer.append((seed, treffer, geprueft))
        print(f"  {seed:>4} {len(geraten):>5} {geprueft:>7} {len(treffer):>8}  {dt:8.1f}")
        if treffer:
            for (ka, kb) in treffer:
                print(f"        -> W{ka//32}.{ka%32}  x  W{kb//32}.{kb%32}")

    print()
    gesamt_paare = sum(g for _, _, g in alle_treffer)
    gesamt_treffer = sum(len(t) for _, t, _ in alle_treffer)
    print(f"  Insgesamt: {gesamt_treffer} neutrale Paare von {gesamt_paare} "
          f"geprueften Paaren ueber {SEEDS} Seeds")
    print(f"  Gesamtzeit: {time.time() - t_start:.1f} s")
