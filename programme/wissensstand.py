"""Wissensstand ueber den Eingaberaum der zweiten SHA-256-Runde."""
import math

print("="*80)
print("1) WIEVIEL DES EINGABERAUMS IST UEBERHAUPT ERKUNDET?")
print("="*80)
# Bitcoin-Gesamtarbeit seit 2009 abschaetzen
# Kumulative Arbeit ~ Difficulty * 2^32 pro Block, summiert
# Naeherung ueber die aktuelle Hashrate und die Wachstumskurve
jahre=[(2009,1e6),(2011,1e10),(2013,1e14),(2015,4e14),(2017,3e18),
       (2019,5e19),(2021,1.5e20),(2023,4e20),(2025,8e20),(2026,9.32e20)]
sek=365.25*24*3600
gesamt=0
for i in range(len(jahre)-1):
    j1,h1=jahre[i]; j2,h2=jahre[i+1]
    mittel=(h1+h2)/2
    gesamt += mittel*(j2-j1)*sek
print(f"  Geschaetzte Gesamtzahl aller je berechneten Bitcoin-Hashes: {gesamt:.3e}")
print(f"  Das entspricht 2^{math.log2(gesamt):.1f}")
print()
raum=2.0**256
print(f"  Eingaberaum der zweiten Runde (32 Byte): 2^256 = {raum:.3e}")
print(f"  Erkundeter Anteil: {gesamt/raum:.3e} = 2^{math.log2(gesamt/raum):.1f}")
print()
print(f"  In Worten: etwa {gesamt/raum*100:.0e} Prozent.")
print("  Zum Vergleich: ein einzelnes Atom im Verhaeltnis zum beobachtbaren")
print(f"  Universum ist ~1e-80 - also {1e-80/(gesamt/raum):.0e} mal GROESSER als")
print("  unser erkundeter Anteil.")
print()

print("="*80)
print("2) WIEVIELE EINGABEWERTE FUEHREN ZU NIEDRIGEN AUSGABEN?")
print("="*80)
print("  Die Zahl ist exakt berechenbar, weil SHA-256 gleichverteilt abbildet.\n")
print(f"  {'fuehrende Nullbits':>19} {'Anteil':>14} {'Eingaben in 2^256':>22}")
for k in [32,64,79,94,128,192,256]:
    anteil=2.0**-k
    anz=2.0**(256-k)
    kom=""
    if k==79: kom="  <- aktuelles Mining-Ziel"
    if k==94: kom="  <- Rekordblock 634.842"
    if k==256: kom="  <- H = 0"
    print(f"  {k:>19} {anteil:>14.3e} {anz:>22.3e}{kom}")
print()
print("  -> Selbst fuer H = 0 existiert erwartungsgemaess 1 Urbild.")
print("     Es gibt also KEINEN Mangel an Loesungen, nur ein Suchproblem.")
print()

print("="*80)
print("3) KANN MAN AUSSCHLIESSEN, DASS EIN AUSGABEWERT MEHRFACH ENTSTEHT?")
print("="*80)
print("  Frage: hat ein gegebener 256-Bit-Ausgabewert mehrere 32-Byte-Urbilder?")
print()
print("  Der Eingaberaum (2^256) und der Ausgaberaum (2^256) sind GLEICH GROSS.")
print("  Bei einer Zufallsabbildung folgt die Zahl der Urbilder einer")
print("  Poisson-Verteilung mit Erwartungswert 1:")
print()
print(f"  {'Urbilder':>10} {'Wahrscheinlichkeit':>20}")
for k in range(5):
    p=math.exp(-1)/math.factorial(k)
    print(f"  {k:>10} {p:>20.4f}")
print()
print("  -> 36,8 % der Ausgabewerte haben GAR KEIN Urbild.")
print("     36,8 % haben genau eines, 18,4 % genau zwei.")
print()
print("  AUSSCHLIESSEN laesst sich Mehrfachheit also NICHT - im Gegenteil,")
print("  bei etwa 26 % der Werte gibt es mindestens zwei Urbilder.")
print("  Nachweisen laesst es sich aber ebenso wenig: man muesste sie finden.")
print()
print("  BEWIESEN haben wir das nur fuer K1-1 (Satz E): dort ist die Abbildung")
print("  auf 65.536 Eingaben injektiv - erschoepfend geprueft.")
print()

print("="*80)
print("4) WAS WIR UEBER DIE BEKANNTEN NIEDRIGEN AUSGABEN WISSEN")
print("="*80)
print("  Datenlage: die 10 niedrigsten Block-Hashes der Historie (Abschnitt 4.6)")
print()
print("  GEPRUEFT und unauffaellig:")
print("    - Bitverteilung nach den fuehrenden Nullen: 0,61 Sigma")
print("    - Hexziffernverteilung: max. 1,78 Sigma")
print("    - Haeufigkeit je zusaetzlicher Hex-Null: Faktor ~16 wie erwartet")
print()
print("  NICHT pruefbar mit vorhandenen Daten:")
print("    - die zugehoerigen Eingangshashes (80-Byte-Header noetig)")
print("    - ob Miner mit bestimmten Header-Mustern bevorzugt gewinnen")
print()
print("  Diese zweite Liste ist der Bereich, in dem tatsaechlich noch")
print("  Spielraum fuer neue Messungen besteht.")
print()

print("="*80)
print("5) SPIELRAUM FUER NEUE ERKENNTNISSE - ehrliche Einschaetzung")
print("="*80)
zeilen=[
 ("Vollstaendig erschoepft", [
   "K1-1 (16 freie Bits): ANF, Kollisionen, Injektivitaet - alles exakt",
   "Konstantenpropagation: maschinelles Optimum erreicht (861 Ops)",
   "Affine Bits: struktureller Beweis, Runde 2 -> 3 scharfer Uebergang",
   "Gatterminimierung: 50 % durch Repraesentationswahl"]),
 ("Quantitativ geschlossen", [
   "Groebner/XL: 1,2e70 Operationen bei Grad 16",
   "GP/Suchverfahren: sechs Methoden, alle auf Kontrollgruppenniveau",
   "Fester Zielhash: Faktor 2^177 gegenueber normalem Mining",
   "Rotationskollisionen: erschoepfend null bei k=24 Bit"]),
 ("Offen und messbar", [
   "Quadratwurzel-Befund (z = -2,70) mit mehr Symmetrieklassen absichern",
   "Blockchain-Header: Nonce-Verteilung, Midstate-Korrelation",
   "Cut-Rewriting mit echter NPN-Bibliothek (ueber die 50 % hinaus)",
   "Rundenreduziertes SHA-256: wo genau steht die Wand?"]),
 ("Offen und NICHT erreichbar", [
   "Untere Schranken fuer Schaltungsgroesse (60-747 Gatter)",
   "Nichtexistenzbeweise fuer Urbilder",
   "Differentielle Pfade ueber Runde 31 hinaus",
   "Jeder Angriff auf volles SHA-256"]),
]
for titel,punkte in zeilen:
    print(f"\n  {titel.upper()}")
    for p in punkte:
        print(f"    - {p}")
print()
print("="*80)
print("KERNZAHL")
print("="*80)
print(f"  Erkundeter Anteil des Eingaberaums nach 17 Jahren Bitcoin: 2^{math.log2(gesamt/raum):.0f}")
print("  Das ist der Grund, warum statistische Aussagen ueber 'welche Eingaben")
print("  fuehren zu niedrigen Ausgaben' nicht moeglich sind: die Stichprobe")
print("  ist im Verhaeltnis zum Raum nicht klein, sondern verschwindend.")
