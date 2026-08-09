"""Direkte Messung der in Abschnitt 16 offen gelassenen Frage: neutrale Bits
bei r = 17.

Abschnitt 20 zeigt: Guess-and-Determine braucht bei r = 17 exakt g(17) = 64
geratene Nachrichtenbits (wortweise Reihenfolge), bis Unit-Propagation den
gesamten Rest des Systems bestimmt. Offen blieb, ob alle 64 Bits dafuer
tatsaechlich noetig sind, oder ob ein Teil davon neutral ist.

Definition (uebertragen aus dem Begriff der neutralen Bits in der
differentiellen Kryptanalyse, Biham/Chen 2004, hier auf Guess-and-Determine
angewandt statt auf ein differentielles Merkmal):

  Ein geratenes Bit i ist NEUTRAL, wenn die Propagation bei allen uebrigen
  63 geratenen Bits auf ihrem Loesungswert auch mit i auf dem GEFLIPPTEN
  Wert konfliktfrei alle Variablen bestimmt.

Ist ein Bit neutral, war sein konkreter Wert fuer das Schliessen des
Systems nicht erforderlich - die tatsaechlich noetige Ratemenge waere
kleiner als g(17) = 64. Nach Abschnitt 16: 32 neutrale Bits wuerden den
Sprung von g(16)=0 auf g(17)=64 auf die erwartete Rate von 32 Bit/Runde
zurueckfuehren; 0 neutrale Bits bestaetigen 64 als eigenstaendigen Befund.

Kontrollen:
  1. Zehn unabhaengige Zufallsinstanzen statt einer einzelnen - ein
     Einzelfund waere kein Strukturbefund (Lehre 1 und 4 des Dokuments).
  2. Positivkontrolle: Bits ausserhalb der Ratemenge sind durch Propagation
     bereits erzwungen und muessen beim Flippen sofort einen Konflikt
     ausloesen - sonst ist die Testmaschinerie fehlerhaft, nicht der Befund
     interessant.

Nutzt ausschliesslich die vorhandene Propagationsmaschine (k1_propagation.py).
Kein externer Solver.
"""
import random, sys
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
    """Wie k1_gnd_kurve.py, Rateordnung 'wort': liefert die frei-Indizes,
    die tatsaechlich geraten werden muessen (nicht bereits durch
    Propagation bestimmt), in Ratereihenfolge."""
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


def neutral_test(F, frei, geraten):
    """Fuer jedes geratene Bit: bleibt die Propagation bei allen uebrigen
    63 Bits auf Loesungswert und diesem einen Bit geflippt konfliktfrei
    und vollstaendig? -> Bit ist neutral."""
    basis = Prop([list(c) for c in F.cls], F.n)
    basis.start()
    m0 = basis.mark()
    ergebnisse = []
    for k_flip in geraten:
        konflikt = False
        for k in geraten:
            l = frei[k]
            soll = F.lv(l)
            if k == k_flip:
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
        neutral = (not konflikt) and basis.offen() == 0
        ergebnisse.append(neutral)
        basis.undo(m0)
    return ergebnisse


def kontrolle_erzwungene_bits(F, frei, geraten, seed, stichprobengroesse=20):
    """Positivkontrolle: Bits ausserhalb der Ratemenge sind bereits durch
    Propagation erzwungen. Sie muessen beim Flippen sofort einen Konflikt
    ausloesen."""
    rng = random.Random(1000 + seed)
    ausserhalb = [k for k in range(len(frei)) if k not in set(geraten)]
    stichprobe = rng.sample(ausserhalb, min(stichprobengroesse, len(ausserhalb)))
    p = Prop([list(c) for c in F.cls], F.n)
    p.start()
    for k in geraten:
        l = frei[k]
        p.entschieden(l if F.lv(l) else -l)
    m = p.mark()
    treffer = 0
    for k in stichprobe:
        l = frei[k]
        lit = -l if F.lv(l) else l  # geflippter (falscher) Wert
        ok = p.entschieden(lit)
        if not ok:
            treffer += 1
        p.undo(m)
    return treffer, len(stichprobe)


print("=" * 76)
print(f"NEUTRALE BITS BEI r = {R}")
print("=" * 76)
print(f"  {'seed':>4} {'g(r)':>5} {'neutral':>8}  Positionen (Wort.Bit)")

alle_neutral_counts = []
for seed in range(SEEDS):
    F, frei = instanz(seed)
    geraten = wortweise_ratemenge(F, frei)
    ergebnisse = neutral_test(F, frei, geraten)
    n_neutral = sum(ergebnisse)
    alle_neutral_counts.append(n_neutral)
    pos = [f"W{geraten[i]//32}.{geraten[i]%32}" for i, e in enumerate(ergebnisse) if e]
    print(f"  {seed:>4} {len(geraten):>5} {n_neutral:>8}  {pos}")

mittel = sum(alle_neutral_counts) / len(alle_neutral_counts)
print()
print(f"  Mittel ueber {SEEDS} Seeds: {mittel:.2f} neutrale Bits von 64")
print(f"  Minimum: {min(alle_neutral_counts)}  Maximum: {max(alle_neutral_counts)}")

print()
print("-" * 76)
print("POSITIVKONTROLLE: erzwungene Bits ausserhalb der Ratemenge")
print("-" * 76)
for seed in range(3):
    F, frei = instanz(seed)
    geraten = wortweise_ratemenge(F, frei)
    treffer, n = kontrolle_erzwungene_bits(F, frei, geraten, seed)
    status = "Testmaschinerie ok" if treffer == n else "ACHTUNG: unerwartet"
    print(f"  seed {seed}: {treffer}/{n} Stichproben-Bits ausserhalb der Ratemenge "
          f"loesen beim Flippen sofort einen Konflikt aus  ({status})")
