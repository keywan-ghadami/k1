"""V1 der Verifikation zu Abschnitt 22.4: Maschinenrauschen von Instanzvarianz
trennen.

Der Messlauf zu 22.4 hat je Zelle genau eine Instanz einmal geloest und aus
den Zeiten eine Rangfolge abgeleitet. Bevor diese Rangfolge ueberhaupt
interpretierbar ist, muss bekannt sein, wie gross die Streuung bei
UNVERAENDERTER Eingabe ist. CaDiCaL ist bei gleicher Eingabe deterministisch;
die hier gemessene Streuung ist daher reines Maschinenrauschen (Taktung,
Cache, Hintergrundlast). Sie ist die Untergrenze fuer jede Aussage ueber
Zeitunterschiede.

Gemessen wird dieselbe CNF-Datei mehrfach, je Variante, in den 9.1-treuen
Kodierungen (Hashing, Baum-Klammerung, korrekt zerlegte Uebertraege).
"""
import argparse, os, random, statistics, sys
sys.path.insert(0, ".")
from k1_cnf import baue, sha_ref
from k1_sat_messlauf import lauf

VARIANTEN = [
    ("aig",         dict(xor_nativ=False, carry_variante="or_gatter")),
    ("xaig_or",     dict(xor_nativ=True,  carry_variante="or_gatter")),
    ("xaig_andmin", dict(xor_nativ=True,  carry_variante="and_minimal")),
]
TREU = dict(hashing=True, assoz="baum")


def erzeuge(name, kw, r, seed):
    rng = random.Random(seed)
    os.makedirs("cnf_v1", exist_ok=True)
    W16 = [rng.getrandbits(32) for _ in range(16)]
    ziel = [rng.getrandbits(32) for _ in range(8)]
    F, frei, H = baue(r, "block", W16, ziel, **{**kw, **TREU})
    datei = f"cnf_v1/{name}_r{r:02d}_s{seed}.cnf"
    with open(datei, "w") as fh:
        fh.write(f"c V1 Wiederholungsmessung, {name}, r={r}, seed={seed}\n")
        fh.write(f"p cnf {F.n} {len(F.cls)}\n")
        for cl in F.cls: fh.write(" ".join(map(str, cl)) + " 0\n")
    return datei, F.n, len(F.cls)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--r", type=int, default=18)
    ap.add_argument("--wdh", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    print("=" * 80)
    print(f"V1  WIEDERHOLUNGSMESSUNG BEI IDENTISCHER EINGABE  (r={a.r}, "
          f"{a.wdh} Laeufe je Variante)")
    print("=" * 80)
    print("  Gleiche Datei, gleicher Solver -> Streuung = reines Maschinenrauschen.")
    print()
    print(f"  {'Variante':<13} {'Vars':>7} {'Klauseln':>9} {'Zeiten (s)':>34} "
          f"{'Median':>9} {'Spanne':>9}")
    for name, kw in VARIANTEN:
        datei, nvar, ncls = erzeuge(name, kw, a.r, a.seed)
        zeiten, status = [], None
        for _ in range(a.wdh):
            st, dt = lauf(a.solver, datei, a.timeout)
            status = st
            zeiten.append(dt)
            if st == "TIMEOUT":
                break
        med = statistics.median(zeiten)
        spanne = (max(zeiten) - min(zeiten)) / med * 100 if med > 0 else 0.0
        zs = "  ".join(f"{z:8.2f}" for z in zeiten)
        marke = "" if status in ("SAT", "UNSAT") else f"  [{status}]"
        print(f"  {name:<13} {nvar:>7} {ncls:>9} {zs:>34} {med:>9.2f} "
              f"{spanne:>8.1f}%{marke}")
        sys.stdout.flush()

    print()
    print("  Deutung: die Spanne ist die Rauschgrenze. Zeitunterschiede zwischen")
    print("  Varianten sind nur dann Befunde, wenn sie deutlich darueber liegen -")
    print("  und auch dann erst nach der Instanzvarianz-Messung (V2/V3).")


if __name__ == "__main__":
    main()
