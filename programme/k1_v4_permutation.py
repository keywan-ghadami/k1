"""V4 der Verifikation zu Abschnitt 22.4: Darstellungsvarianz.

Die Kontrollkette V1-V3 hat zwei Streuungsquellen vermessen:

  V1  gleiche Datei, gleicher Solver          -> 0,7-1,8 %  (Maschinenrauschen)
  V2/V3  verschiedene Instanzen, gleiche Kodierung -> Faktor 2-4 (r=17)
                                                      Faktor 32  (r=18)

Dazwischen fehlt eine dritte Quelle, und zwar genau die, die der
Kodierungsvergleich unkontrolliert mitmisst:

  V4  GLEICHE Instanz, GLEICHE Kodierung, nur andere DARSTELLUNG
      (Variablennumerierung, Klauselreihenfolge, Literalreihenfolge)

CDCL-Solver sind gegen die Darstellung nicht invariant: Verzweigungsheuristik,
Klauseldatenbank und Vorverarbeitung haengen an der Reihenfolge, in der
Variablen und Klauseln auftreten. Eine Permutation aendert die Aufgabe nicht -
sie ist erfuellbarkeitserhaltend und bildet Loesungen bijektiv aufeinander ab -
aber sie kann die Laufzeit verschieben.

Das ist hier kein akademischer Punkt: Die drei Kodierungsvarianten aus 22.4
erzeugen zwangslaeufig VERSCHIEDENE Variablennumerierungen und
Klauselreihenfolgen. Ein gemessener Zeitunterschied zwischen ihnen ist deshalb
nur dann ein Kodierungseffekt, wenn er die Darstellungsvarianz uebersteigt.
Ohne V4 ist der Kodierungsvergleich nicht interpretierbar - in beide
Richtungen: ein Nullbefund kann echte Effekte verdecken, ein Positivbefund
kann reine Permutationsstreuung sein.

Aufruf:
    python3 k1_v4_permutation.py --r 17 --perms 10 --timeout 300
"""
import argparse, math, os, random, statistics, sys, time
sys.path.insert(0, ".")
from k1_cnf import baue
from k1_sat_messlauf import lauf

VARIANTEN = [
    ("aig",         dict(xor_nativ=False, carry_variante="or_gatter")),
    ("xaig_or",     dict(xor_nativ=True,  carry_variante="or_gatter")),
    ("xaig_andmin", dict(xor_nativ=True,  carry_variante="and_minimal")),
]
TREU = dict(hashing=True, assoz="baum")
AUS = "cnf_v4"


def cnf_bauen(kw, r, seed):
    """Instanz wie in k1_v2_instanzvarianz.erzeuge - gleiche Seed-Ableitung,
    damit die Zahlen unmittelbar vergleichbar sind."""
    rng = random.Random(100000 + seed)
    W16 = [rng.getrandbits(32) for _ in range(16)]
    ziel = [rng.getrandbits(32) for _ in range(8)]
    F, frei, H = baue(r, "block", W16, ziel, **{**kw, **TREU})
    return F.n, [list(c) for c in F.cls]


def permutieren(n, cls, rng):
    """Erfuellbarkeitserhaltende Permutation: Variablen umnumerieren,
    Klauseln mischen, Literale innerhalb der Klauseln mischen.
    Die Aufgabe bleibt dieselbe, nur ihre Darstellung aendert sich."""
    perm = list(range(1, n + 1))
    rng.shuffle(perm)
    ab = {v: perm[v-1] for v in range(1, n + 1)}
    neu = []
    for c in cls:
        d = [(ab[abs(l)] if l > 0 else -ab[abs(l)]) for l in c]
        rng.shuffle(d)
        neu.append(d)
    rng.shuffle(neu)
    return neu


def schreiben(datei, n, cls, kopf):
    os.makedirs(os.path.dirname(datei), exist_ok=True)
    with open(datei, "w") as fh:
        fh.write(f"c {kopf}\n")
        fh.write(f"p cnf {n} {len(cls)}\n")
        for c in cls:
            fh.write(" ".join(map(str, c)) + " 0\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r", type=int, default=17)
    ap.add_argument("--perms", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0, help="Instanz-Seed")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--solver", default="cadical195,kissat404")
    ap.add_argument("--varianten", default="aig,xaig_or,xaig_andmin")
    a = ap.parse_args()
    solver = [s.strip() for s in a.solver.split(",") if s.strip()]
    gewaehlt = [v.strip() for v in a.varianten.split(",") if v.strip()]

    print("=" * 84)
    print(f"V4  DARSTELLUNGSVARIANZ, r={a.r}, Instanz-Seed {a.seed}, "
          f"{a.perms} Permutationen")
    print("=" * 84)
    print("  Identische Instanz, identische Kodierung, nur umnumeriert und")
    print("  umgeordnet. Jede Abweichung ist reine Darstellungsvarianz.")
    print(f"  Vergleichsgroessen: Maschinenrauschen (V1) 0,7-1,8 %;")
    print(f"  Instanzvarianz (V2/V3) Faktor 2-4 bei r=17, Faktor 32 bei r=18.")
    print()

    ergebnis = {}
    for nm, kw in VARIANTEN:
        if nm not in gewaehlt: continue
        n, cls = cnf_bauen(kw, a.r, a.seed)
        for sv in solver:
            zeiten, tos = [], 0
            for i in range(a.perms):
                rng = random.Random(7000 + i)
                # i = 0 ist die Identitaet: der unveraenderte Referenzlauf
                pc = cls if i == 0 else permutieren(n, cls, rng)
                datei = f"{AUS}/{nm}_r{a.r:02d}_s{a.seed}_p{i:02d}.cnf"
                schreiben(datei, n, pc, f"V4 {nm} r={a.r} perm={i}")
                st, dt = lauf(sv, datei, a.timeout)
                if st not in ("SAT", "UNSAT"): tos += 1
                zeiten.append(dt)
                print(f"    {nm:<13} {sv:<11} perm {i:>2}  {dt:>8.2f}s  {st}")
                sys.stdout.flush()
            ergebnis[(nm, sv)] = (zeiten, tos)

    print()
    print("-" * 84)
    print("STREUUNG DURCH REINE UMNUMERIERUNG")
    print("-" * 84)
    print(f"  {'Variante':<13} {'Solver':<12} {'min':>8} {'Median':>8} {'max':>8} "
          f"{'max/min':>9} {'Timeouts':>9}")
    for (nm, sv), (zs, tos) in ergebnis.items():
        f = max(zs) / min(zs) if min(zs) > 0 else float("inf")
        print(f"  {nm:<13} {sv:<12} {min(zs):>8.2f} {statistics.median(zs):>8.2f} "
              f"{max(zs):>8.2f} {f:>8.2f}x {tos:>9}")

    print()
    print("  Lesart: liegt max/min hier in derselben Groessenordnung wie die in")
    print("  22.4 berichteten Unterschiede zwischen Kodierungen, dann misst der")
    print("  Kodierungsvergleich ueberwiegend Darstellung und nicht Kodierung.")


if __name__ == "__main__":
    main()
