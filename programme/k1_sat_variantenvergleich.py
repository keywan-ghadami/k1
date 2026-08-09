"""Erweiterung von Abschnitt 17.4/22 um einen Kodierungsvarianten-Vergleich.

Abschnitt 22 kalibriert genau eine CNF-Kodierung (natives XOR, Tseitin-Maj-
Uebertrag) gegen CaDiCaL/Kissat: r=18 loesbar, r=19 Timeout. Abschnitt 9.1
katalogisiert mehrere Verdrahtungsvarianten mit sehr unterschiedlicher
Gesamtgroesse (AIG-Basis 198.167, XAIG/OR-Uebertrag 98.899, XAIG/AND-minimal
106.606 Gatter fuer 64 Runden) - aber immer nur als Gatterzahl gemessen, nie
gegen einen echten Solver.

Dieses Skript baut alle drei Varianten mit derselben k1_cnf.CNF-Klasse
(Parameter xor_nativ / carry_variante), erzeugt fuer jede echte
Zufallsziel-Instanzen (Modell 'block', wie in Abschnitt 22) ueber denselben
Rundenzahlbereich und faehrt dieselbe Kalibrierung. Damit wird aus der
Prognose in 9.11 ("null bis eine Runde Effekt") eine Messung mit mehr als
zwei Punkten: nicht nur kleiner-vs-groesser, sondern eine Kurve ueber drei
tatsaechlich unterschiedliche Verdrahtungen, die zusaetzlich die Frage
beantwortet, ob Gesamtgroesse oder AND-Zahl (multiplikative Komplexitaet)
die SAT-Schwierigkeit besser vorhersagt - die AND-minimale Form hat weniger
AND-Gatter, aber mehr Gatter insgesamt als die OR-Uebertrag-Form.

Aufruf:
    python3 k1_sat_variantenvergleich.py --timeout 600 --runden 16,17,18,19
"""
import argparse, os, random, sys, time
sys.path.insert(0, ".")
from k1_cnf import baue, sha_ref
from k1_sat_messlauf import lauf

VARIANTEN = [
    ("aig",        dict(xor_nativ=False, carry_variante="or")),
    ("xaig_or",     dict(xor_nativ=True,  carry_variante="or")),
    ("xaig_andmin", dict(xor_nativ=True,  carry_variante="and_minimal")),
]


def erzeuge(name, kw, runden, seed=0):
    rng = random.Random(seed)
    os.makedirs("cnf_varianten", exist_ok=True)
    dateien = []
    for r in runden:
        W16 = [rng.getrandbits(32) for _ in range(16)]
        ziel = [rng.getrandbits(32) for _ in range(8)]
        F, frei, H = baue(r, "block", W16, ziel, **kw)
        datei = f"cnf_varianten/{name}_r{r:02d}.cnf"
        with open(datei, "w") as fh:
            fh.write(f"c K1 Variantenvergleich, {name}, {r} Runden, Zufallsziel\n")
            fh.write(f"p cnf {F.n} {len(F.cls)}\n")
            for cl in F.cls: fh.write(" ".join(map(str, cl)) + " 0\n")
        dateien.append((r, datei, F.n, len(F.cls)))
    return dateien


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--runden", default="16,17,18,19")
    a = ap.parse_args()
    runden = [int(x) for x in a.runden.split(",")]

    print("=" * 84)
    print("VARIANTENVERGLEICH: Kodierungsgroesse vs. tatsaechliche CDCL-Loesbarkeit")
    print("=" * 84)
    print(f"Solver: {a.solver}   Timeout: {a.timeout}s   Runden: {runden}")
    print()

    gesamt = {}
    for name, kw in VARIANTEN:
        print("-" * 84)
        print(f"Variante: {name}  (xor_nativ={kw['xor_nativ']}, carry={kw['carry_variante']})")
        print("-" * 84)
        dateien = erzeuge(name, kw, runden)
        print(f"  {'Runden':>7} {'Vars':>8} {'Klauseln':>9} {'Status':>10} {'Zeit/s':>10}")
        ergebnisse = []
        for r, datei, nvar, ncls in dateien:
            st, dt = lauf(a.solver, datei, a.timeout)
            print(f"  {r:>7} {nvar:>8} {ncls:>9} {st:>10} {dt:>10.2f}")
            ergebnisse.append((r, nvar, ncls, st, dt))
            if st == "TIMEOUT":
                break
        gesamt[name] = ergebnisse
        print()

    print("=" * 84)
    print("ZUSAMMENFASSUNG")
    print("=" * 84)
    print(f"  {'Variante':<14} {'max. r geloest':>16} {'Zeit bei max r':>16}")
    for name, ergebnisse in gesamt.items():
        gel = [e for e in ergebnisse if e[3] in ("SAT", "UNSAT")]
        if gel:
            r, nvar, ncls, st, dt = gel[-1]
            print(f"  {name:<14} {r:>16} {dt:>15.2f}s")
        else:
            print(f"  {name:<14} {'keine':>16} {'':>16}")


if __name__ == "__main__":
    main()
