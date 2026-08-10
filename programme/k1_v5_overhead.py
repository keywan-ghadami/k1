"""V5 der Verifikation zu Abschnitt 22.4: Was misst der Timer eigentlich?

`k1_sat_messlauf.lauf` startet den Zeitnehmer VOR dem Kindprozess:

    t0 = time.time()
    p.start()          # Spawn eines frischen Python-Interpreters
    p.join(timeout)    # darin: import pysat, CNF(from_file=...), bootstrap, solve

Gemessen ist damit nicht die Loesungszeit, sondern

    Spawn + Interpreterstart + Parsen der DIMACS-Datei + Bootstrap + Loesen.

Alle Summanden ausser dem letzten wachsen mit der Klauselzahl - also mit genau
der Groesse, deren Einfluss 22.4 untersucht. Das ist keine Zufallsstoerung,
sondern eine systematische Verzerrung entlang der Untersuchungsachse: Die
groesste Kodierung (`aig`, 143.075 Klauseln bei r=18) traegt zwangslaeufig mehr
Overhead als die kleinste (`xaig_or`, 84.233).

22.4 schaetzt diesen Anteil bei r = 17 auf 7-10 %. Dieses Skript misst ihn
statt ihn zu schaetzen: derselbe Kindprozess-Pfad, dieselbe Datei, nur ohne
den Aufruf von solve().

Aufruf:
    python3 k1_v5_overhead.py --r 17
    python3 k1_v5_overhead.py --r 18 --timeout 900
"""
import argparse, multiprocessing, os, random, statistics, sys, time
sys.path.insert(0, ".")
from k1_cnf import baue
from k1_sat_messlauf import lauf

VARIANTEN = [
    ("aig",         dict(xor_nativ=False, carry_variante="or_gatter")),
    ("xaig_or",     dict(xor_nativ=True,  carry_variante="or_gatter")),
    ("xaig_andmin", dict(xor_nativ=True,  carry_variante="and_minimal")),
]
TREU = dict(hashing=True, assoz="baum")
AUS = "cnf_v5"


def _leer_worker(solver_name, datei, q):
    """Identisch zu k1_sat_messlauf._solve_worker, nur ohne s.solve()."""
    from pysat.formula import CNF
    from pysat.solvers import Solver
    cnf = CNF(from_file=datei)
    with Solver(name=solver_name, bootstrap_with=cnf.clauses) as s:
        q.put("BEREIT")


def overhead(solver, datei):
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_leer_worker, args=(solver, datei, q))
    t0 = time.time()
    p.start()
    p.join()
    dt = time.time() - t0
    if not q.empty(): q.get()
    return dt


def erzeuge(name, kw, r, seed):
    """Instanz-Ableitung identisch zu k1_v2_instanzvarianz.erzeuge."""
    rng = random.Random(100000 + seed)
    W16 = [rng.getrandbits(32) for _ in range(16)]
    ziel = [rng.getrandbits(32) for _ in range(8)]
    F, frei, H = baue(r, "block", W16, ziel, **{**kw, **TREU})
    os.makedirs(AUS, exist_ok=True)
    datei = f"{AUS}/{name}_r{r:02d}_s{seed:03d}.cnf"
    with open(datei, "w") as fh:
        fh.write(f"c V5 Overhead, {name}, r={r}, seed={seed}\n")
        fh.write(f"p cnf {F.n} {len(F.cls)}\n")
        for cl in F.cls: fh.write(" ".join(map(str, cl)) + " 0\n")
    return datei, F.n, len(F.cls)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r", type=int, default=17)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--wdh", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--solver", default="cadical195,kissat404")
    a = ap.parse_args()
    solver = [s.strip() for s in a.solver.split(",") if s.strip()]

    print("=" * 88)
    print(f"V5  OVERHEAD-ANTEIL AN DER GEMESSENEN ZEIT, r={a.r}")
    print("=" * 88)
    print("  Overhead = Spawn + Interpreterstart + DIMACS-Parsen + Bootstrap,")
    print("  gemessen ueber denselben Kindprozess-Pfad ohne solve().")
    print()
    print(f"  {'Variante':<13} {'Solver':<12} {'Klauseln':>9} {'Overhead':>10} "
          f"{'Gesamt':>10} {'Anteil':>8} {'Rest=Loesen':>12}")
    tab = {}
    for seed in range(a.seeds):
        for nm, kw in VARIANTEN:
            datei, nvar, ncls = erzeuge(nm, kw, a.r, seed)
            for sv in solver:
                ov = statistics.median([overhead(sv, datei) for _ in range(a.wdh)])
                ges = statistics.median([lauf(sv, datei, a.timeout)[1]
                                         for _ in range(a.wdh)])
                anteil = 100.0 * ov / ges if ges > 0 else float("nan")
                tab.setdefault((nm, sv), []).append((ov, ges))
                print(f"  {nm:<13} {sv:<12} {ncls:>9} {ov:>9.2f}s {ges:>9.2f}s "
                      f"{anteil:>7.1f}% {ges-ov:>11.2f}s")
                sys.stdout.flush()
        print()

    print("-" * 88)
    print("ZUSAMMENFASSUNG (Median ueber Instanzen)")
    print("-" * 88)
    print(f"  {'Variante':<13} {'Solver':<12} {'Overhead':>10} {'Gesamt':>10} "
          f"{'Anteil':>8} {'reine Loesezeit':>16}")
    rein = {}
    for (nm, sv), ds in tab.items():
        ov = statistics.median([o for o, _ in ds])
        ge = statistics.median([g for _, g in ds])
        rein[(nm, sv)] = ge - ov
        print(f"  {nm:<13} {sv:<12} {ov:>9.2f}s {ge:>9.2f}s "
              f"{100*ov/ge:>7.1f}% {ge-ov:>15.2f}s")

    print()
    print("-" * 88)
    print("WIRKUNG AUF DEN VERGLEICH: gemessene gegen bereinigte Rangfolge")
    print("-" * 88)
    for sv in solver:
        namen = [nm for nm, _ in VARIANTEN if (nm, sv) in tab]
        if len(namen) < 2: continue
        ges = {nm: statistics.median([g for _, g in tab[(nm, sv)]]) for nm in namen}
        print(f"  Solver {sv}:")
        for i in range(len(namen)):
            for j in range(i+1, len(namen)):
                a_, b_ = namen[i], namen[j]
                fg = ges[b_] / ges[a_] if ges[a_] > 0 else float("nan")
                fr = (rein[(b_, sv)] / rein[(a_, sv)]
                      if rein[(a_, sv)] > 0 else float("nan"))
                print(f"    {a_:<13} vs {b_:<13} Faktor gemessen {fg:>6.2f}x   "
                      f"nach Abzug des Overheads {fr:>6.2f}x")
    print()
    print("  Lesart: weicht die bereinigte Rangfolge von der gemessenen ab, hat")
    print("  22.4 (und die V2-Aussage 'aig zuverlaessig langsamer') teilweise")
    print("  Dateigroesse gemessen statt Solverschwierigkeit.")


if __name__ == "__main__":
    main()
