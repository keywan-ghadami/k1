"""V2/V3 der Verifikation zu Abschnitt 22.4: Instanzvarianz und Solverabhaengigkeit.

V1 hat gezeigt, dass das Maschinenrauschen bei 1-2 % liegt - Wiederholungslaeufe
auf derselben Datei sind also nicht die Fehlerquelle. Offen bleibt die
Instanzvarianz: CDCL-Laufzeiten auf erfuellbaren Instanzen sind schwerschwaenzig,
und der bisherige Befund beruht je Zelle auf genau einer Instanz.

Aufbau:
  - N unabhaengige Zufallsziel-Instanzen je Kodierungsvariante.
  - Jede Instanz wird von JEDEM Solver geloest (verschraenkt, nicht in
    getrennten Durchgaengen). Dadurch sind die Daten GEPAART: die Schwierigkeit
    der einzelnen Instanz faellt als Stoergroesse heraus.
  - Streng sequenziell, damit die 1-2 % Rauschgrenze aus V1 gilt.

Auswertung:
  - Median und Interquartilsabstand statt Mittelwert (schwerschwaenzig).
  - Vorzeichentest auf gepaarten Seeds als eigentlicher Test: in wie vielen
    Instanzen schlaegt Variante A die Variante B? Das ist gegen die
    Verteilungsform robust und vertraegt zensierte Werte (ein Timeout ist ein
    gueltiger Rang "langsamer als die Grenze").
  - Timeouts werden gezaehlt und als zensiert ausgewiesen, nicht als Zahl
    verrechnet.

Aufruf:
    python3 k1_v2_instanzvarianz.py --r 17 --seeds 40 --timeout 300
    python3 k1_v2_instanzvarianz.py --r 18 --seeds 15 --timeout 900
"""
import argparse, itertools, math, os, random, statistics, sys
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
    """Eine Instanz je (Variante, Seed). Das Ziel haengt nur vom Seed ab, damit
    alle Varianten bei gleichem Seed dieselbe Aufgabe kodieren."""
    rng = random.Random(100000 + seed)
    W16 = [rng.getrandbits(32) for _ in range(16)]
    ziel = [rng.getrandbits(32) for _ in range(8)]
    F, frei, H = baue(r, "block", W16, ziel, **{**kw, **TREU})
    os.makedirs("cnf_v2", exist_ok=True)
    datei = f"cnf_v2/{name}_r{r:02d}_s{seed:03d}.cnf"
    with open(datei, "w") as fh:
        fh.write(f"c V2 Instanzvarianz, {name}, r={r}, seed={seed}\n")
        fh.write(f"p cnf {F.n} {len(F.cls)}\n")
        for cl in F.cls: fh.write(" ".join(map(str, cl)) + " 0\n")
    return datei


def quartile(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0: return (None, None, None)
    med = statistics.median(s)
    q1 = statistics.median(s[:n//2]) if n > 1 else s[0]
    q3 = statistics.median(s[(n+1)//2:]) if n > 1 else s[0]
    return q1, med, q3


def vorzeichentest(k, n):
    """Zweiseitiger exakter Binomialtest gegen p=1/2, ohne scipy."""
    if n == 0: return 1.0
    k = min(k, n - k)
    s = sum(math.comb(n, i) for i in range(k + 1))
    return min(1.0, 2.0 * s / (2 ** n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r", type=int, default=17)
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--solver", default="cadical195,kissat404")
    a = ap.parse_args()
    solver = [s.strip() for s in a.solver.split(",") if s.strip()]

    print("=" * 86)
    print(f"V2/V3  INSTANZVARIANZ, r={a.r}, {a.seeds} Instanzen, "
          f"Solver: {', '.join(solver)}")
    print("=" * 86)
    print(f"  Gepaart: jede Instanz von jedem Solver. Sequenziell. "
          f"Timeout {a.timeout}s.")
    print(f"  Rauschgrenze aus V1: 1-2 %.")
    print()
    kopf = f"  {'seed':>4}"
    for nm, _ in VARIANTEN:
        for sv in solver:
            kopf += f" {nm[:7]+'/'+sv[:3]:>13}"
    print(kopf)

    # zeiten[(variante, solver)] = Liste von (seed, zeit, status)
    zeiten = {(nm, sv): [] for nm, _ in VARIANTEN for sv in solver}
    for seed in range(a.seeds):
        zeile = f"  {seed:>4}"
        for nm, kw in VARIANTEN:
            datei = erzeuge(nm, kw, a.r, seed)
            for sv in solver:
                st, dt = lauf(sv, datei, a.timeout)
                zeiten[(nm, sv)].append((seed, dt, st))
                mark = "" if st in ("SAT", "UNSAT") else "!"
                zeile += f" {dt:>12.2f}{mark}"
        print(zeile)
        sys.stdout.flush()

    print()
    print("-" * 86)
    print("VERTEILUNG (Median, Interquartilsabstand; ! = zensierte Werte enthalten)")
    print("-" * 86)
    print(f"  {'Variante':<13} {'Solver':<12} {'min':>9} {'Q1':>9} {'Median':>9} "
          f"{'Q3':>9} {'max':>9} {'Timeouts':>9}")
    for nm, _ in VARIANTEN:
        for sv in solver:
            ds = zeiten[(nm, sv)]
            ts = [d for _, d, _ in ds]
            nto = sum(1 for _, _, st in ds if st not in ("SAT", "UNSAT"))
            q1, med, q3 = quartile(ts)
            print(f"  {nm:<13} {sv:<12} {min(ts):>9.2f} {q1:>9.2f} {med:>9.2f} "
                  f"{q3:>9.2f} {max(ts):>9.2f} {nto:>9}")

    print()
    print("-" * 86)
    print("GEPAARTER VORZEICHENTEST je Solver (wie oft ist A schneller als B?)")
    print("-" * 86)
    for sv in solver:
        print(f"  Solver {sv}:")
        for (na, _), (nb, _) in itertools.combinations(VARIANTEN, 2):
            da = {s: d for s, d, _ in zeiten[(na, sv)]}
            db = {s: d for s, d, _ in zeiten[(nb, sv)]}
            gem = sorted(set(da) & set(db))
            siege = sum(1 for s in gem if da[s] < db[s])
            n = len(gem)
            faktoren = [db[s] / da[s] for s in gem if da[s] > 0]
            medf = statistics.median(faktoren) if faktoren else float("nan")
            p = vorzeichentest(siege, n)
            print(f"    {na:<13} schneller als {nb:<13} in {siege:>3}/{n:<3} "
                  f"Instanzen   Medianfaktor {medf:>7.2f}x   p = {p:.2e}")

    print()
    print("  Lesart: nur wenn der Vorzeichentest deutlich ausfaellt UND der")
    print("  Medianfaktor die Rauschgrenze klar uebersteigt, ist ein")
    print("  Zeitunterschied zwischen Kodierungen ein Befund.")


if __name__ == "__main__":
    main()
