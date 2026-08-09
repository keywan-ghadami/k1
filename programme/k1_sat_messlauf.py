"""Messlauf der Kalibrierung (Abschnitt 17.3).

Laesst einen CDCL-SAT-Solver ueber die von k1_sat_kodierung.py erzeugten
Instanzen laufen, protokolliert Loesungszeiten und passt den Exponenten an.

Solver kommen ueber das PySAT-Paket (`pip install python-sat`) als
vorkompilierte In-Prozess-Bindings mit, kein Solver-Binary auf dem PATH
noetig. Verfuegbare Namen u.a.: cadical195, cadical153, kissat404, glucose4,
maplechrono, minisat22 (siehe pysat.solvers.SolverNames). Der Timeout wird
per Kindprozess erzwungen, da die C-Loeser selbst kein Timeout kennen.

Aufruf:
    python3 k1_sat_messlauf.py --solver cadical195 --timeout 300
    python3 k1_sat_messlauf.py --solver kissat404 --timeout 600 --wdh 1

Erwartet die CNF-Dateien im Unterverzeichnis cnf/.
"""
import argparse, glob, json, math, multiprocessing, re, statistics, sys, time

def _solve_worker(solver_name, datei, q):
    from pysat.formula import CNF
    from pysat.solvers import Solver
    cnf = CNF(from_file=datei)
    with Solver(name=solver_name, bootstrap_with=cnf.clauses) as s:
        q.put("SAT" if s.solve() else "UNSAT")

def lauf(solver, datei, timeout):
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_solve_worker, args=(solver, datei, q))
    t0 = time.time()
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return "TIMEOUT", float(timeout)
    dt = time.time() - t0
    if not q.empty():
        return q.get(), dt
    return "UNBEKANNT", dt

def fit(punkte):
    """log2(t) = alpha * r + beta, kleinste Quadrate. Gibt (alpha, beta, R2)."""
    pts = [(r, math.log2(max(t, 1e-4))) for r, t in punkte]
    n = len(pts)
    if n < 3: return None
    mx = sum(r for r,_ in pts)/n; my = sum(y for _,y in pts)/n
    sxx = sum((r-mx)**2 for r,_ in pts)
    sxy = sum((r-mx)*(y-my) for r,y in pts)
    if sxx == 0: return None
    a = sxy/sxx; b = my - a*mx
    ss_res = sum((y - (a*r+b))**2 for r,y in pts)
    ss_tot = sum((y-my)**2 for _,y in pts)
    r2 = 1 - ss_res/ss_tot if ss_tot else 1.0
    return a, b, r2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--wdh", type=int, default=3, help="Instanzen je Rundenzahl")
    ap.add_argument("--muster", default="cnf/echt_block_r*.cnf")
    ap.add_argument("--out", default="kalibrierung.json")
    a = ap.parse_args()

    dateien = sorted(glob.glob(a.muster))
    if not dateien:
        print(f"Keine Instanzen unter {a.muster}. Zuerst k1_sat_kodierung.py laufen lassen.")
        sys.exit(1)

    erg, punkte = [], []
    print(f"Solver: {a.solver}   Timeout: {a.timeout}s   Instanzen: {len(dateien)}")
    print(f"{'Runden':>7} {'Status':>10} {'Zeit/s':>12} {'Bemerkung':>22}")
    for d in dateien:
        r = int(re.search(r"r(\d+)\.cnf$", d).group(1))
        zeiten, status = [], None
        for _ in range(a.wdh):
            st, dt = lauf(a.solver, d, a.timeout)
            zeiten.append(dt); status = st
            if st == "TIMEOUT": break
        t = statistics.median(zeiten)
        bem = ""
        if status == "TIMEOUT": bem = "Grenze erreicht"
        elif r <= 16:           bem = "Positivkontrolle"
        print(f"{r:>7} {status:>10} {t:>12.3f} {bem:>22}")
        erg.append({"runden": r, "status": status, "zeit": t, "datei": d})
        if status in ("SAT", "UNSAT") and r >= 17:
            punkte.append((r, t))
        if status == "TIMEOUT":
            print(f"\nReichweite dieser Werkzeugkette: {r-1} Runden "
                  f"(bei {a.timeout}s Grenze).")
            break

    f = fit(punkte)
    print()
    if f:
        alpha, beta, r2 = f
        print(f"Anpassung log2(t) = {alpha:.3f}*r + {beta:.3f}   R^2 = {r2:.4f}")
        print(f"  -> jede zusaetzliche Runde kostet Faktor {2**alpha:.2f}")
        for ziel in (24, 28, 31):
            t = 2**(alpha*ziel + beta)
            print(f"  -> Hochrechnung r={ziel}: {t:.3g} s "
                  f"({t/3.15e7:.3g} Jahre)" if t > 3.15e7 else
                  f"  -> Hochrechnung r={ziel}: {t:.3g} s")
    else:
        print("Zu wenige Datenpunkte ab r=17 fuer eine Anpassung.")

    json.dump(erg, open(a.out, "w"), indent=1)
    print(f"\nRohdaten in {a.out}")
    print("\nEinordnung gegen die Literatur:")
    print("  praktische SAT-Preimages: 17-18 Runden (19 abgeschwaecht)")
    print("  praktische Kollisionen:   31 Runden (ASIACRYPT 2024)")
    print("  theoretische MITM/Biclique-Preimages: bis ~45 Schritte,")
    print("  aber mit Komplexitaet knapp unter 2^256, also ohne echten Gewinn.")

if __name__ == "__main__":
    main()
