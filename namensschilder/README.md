
Mit diesem Tex können die Namensschilder für die Lenyards erzeugt
werden.

Als ersten Schitt muss aus Pretix ein Komplettexport als JSON-Datei
erstellt werden. Diesen kopiert man nach bin/pretixdata.json und
startet das convert.py skript. Das Skript benötigt python3 und muss
unter Umständen noch manuell leicht angepasst werden. Z.B. müssen die
korrekten IDs in die ids-Liste eingetragen werden. Das sind alle ids
die mit Konferenztickets assoziiert sind (Frühbucherticket,
Studierendenticket,...). Heraus fällt pretix.csv

Als zweiter Schritt muss mit pdflatex namensschilder.tex ein PDF mit
den Namensschildern erzeugt werden. Das tex kann bei Bedarf angepasst
werden, vor allem muss aber in der Zeile mit DTLforeach die
auszuwählenden Spaltennamen angepasst werden.

Aktuell wird pro Zeile der Name zwei mal ausgegeben, damit man das
Namensschild knicken kann und hinten und vorne beschriftet ist und man
in die Mitte noch Zusatzzettel (z.B. die Tokens für die Umfrage)
einlegen kann.

Achtung: Das lesen der CSV-Datei und Erstellen des PDFs dauert
lange. Zum schnelleren Testen sollte man sich daher eine
Test-CSV-Datei mit nur wenigen Zeilen zurecht legen.
