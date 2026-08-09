"""Vorschlag durchgerechnet: fester Zielhash statt Target-Bereich."""
import math

print("="*74)
print("DEIN VORSCHLAG, DURCHGERECHNET")
print("="*74)
print("  Idee: nimm den Block mit den meisten fuehrenden Nullen aller Zeiten,")
print("  setze dessen Hash als FESTES Ziel, spare den zweiten SHA-Durchlauf.")
print()

# Realistische Groessenordnungen
netz_hashrate = 932e18          # 932 EH/s
sek_pro_jahr  = 365.25*24*3600
netz_pro_jahr = netz_hashrate*sek_pro_jahr

print("  A) NORMALES MINING (Target-Bereich)")
schwierigkeit_bits = 79
versuche_normal = 2**schwierigkeit_bits
print(f"     Ziel: irgendein Hash mit ~{schwierigkeit_bits} fuehrenden Nullbits")
print(f"     Erwartete Versuche: 2^{schwierigkeit_bits} = {versuche_normal:.3e}")
print(f"     Netzwerk schafft das in: {versuche_normal/netz_hashrate/60:.1f} Minuten")
print()

print("  B) DEIN VORSCHLAG (fester Zielhash)")
print(f"     Ziel: GENAU EIN bestimmter 256-Bit-Wert")
print(f"     Erwartete Versuche: 2^256 = {2.0**256:.3e}")
print(f"     Netzwerk (932 EH/s) braucht: {2.0**256/netz_pro_jahr:.3e} Jahre")
print(f"     Alter des Universums:        1.4e10 Jahre")
print(f"     Faktor:                      {2.0**256/netz_pro_jahr/1.4e10:.2e} mal laenger")
print()

print("  C) DER VERGLEICH")
faktor = 2.0**(256-schwierigkeit_bits)
print(f"     Dein Vorschlag ist 2^{256-schwierigkeit_bits} = {faktor:.3e} mal schwerer")
print(f"     als das, was das Netzwerk gerade alle 10 Minuten schafft.")
print()

print("="*74)
print("WARUM DER GROSSE EINGABERAUM NICHT HILFT")
print("="*74)
print("  Du nennst als Freiheitsgrade: Nonce, Transaktionsauswahl, Version, Zeit.")
nonce=32; version=16; zeit=20
print(f"     Nonce:              2^{nonce}")
print(f"     Version-Rolling:    2^{version}")
print(f"     Zeitstempel:        2^{zeit} (grosszuegig)")
tx_kombis = 200
print(f"     Transaktionsauswahl: 2^{tx_kombis} (extrem grosszuegig gerechnet)")
gesamt = nonce+version+zeit+tx_kombis
print(f"     SUMME:              2^{gesamt}")
print()
print(f"  Benoetigt fuer einen festen Zielhash: 2^256")
print(f"  Dein Suchraum:                       2^{gesamt}")
if gesamt < 256:
    print(f"  -> Der Suchraum ist um Faktor 2^{256-gesamt} = {2.0**(256-gesamt):.2e} ZU KLEIN.")
    print(f"     Selbst wenn du ihn VOLLSTAENDIG durchsuchst, ist die")
    print(f"     Wahrscheinlichkeit eines Treffers {2.0**(gesamt-256):.2e}.")
print()

print("="*74)
print("DER ENTSCHEIDENDE PUNKT")
print("="*74)
print("  Es gibt keinen Grund anzunehmen, dass ein Urbild fuer diesen")
print("  bestimmten Zielhash in deinem Suchraum ueberhaupt EXISTIERT.")
print()
print(f"  Erwartete Zahl der Loesungen im Suchraum: 2^{gesamt} / 2^256 = {2.0**(gesamt-256):.2e}")
print()
print("  Bei normalem Mining ist das anders: dort gibt es ca. 2^177 gueltige")
print("  Hashes, also findet man im selben Suchraum erwartungsgemaess viele.")
print()
print("  ZUSAMMENFASSUNG: der Vorschlag tauscht ein loesbares Problem")
print("  (irgendeiner von 2^177 Treffern) gegen ein unloesbares")
print("  (genau ein bestimmter Treffer, der wahrscheinlich gar nicht")
print("  im erreichbaren Raum liegt).")
