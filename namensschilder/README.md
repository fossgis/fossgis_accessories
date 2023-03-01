
Mit diesem Tex können die Namensschilder für die Lanyards erzeugt
werden.

1. Als ersten Schitt muss aus Pretix ein Komplettexport als JSON-Datei
erstellt werden. Diesen kopiert man nach bin/pretixdata.json

z.B. für 2018
https://pretix.eu/control/event/fossgis/konf-2018/orders/export/

2. Start des convert.py skripts. Das Skript benötigt python3 und muss
unter Umständen noch manuell leicht angepasst werden. Z.B. müssen die
korrekten IDs in die ids-Liste eingetragen werden. Das sind alle ids
die mit Konferenztickets assoziiert sind (Frühbucherticket,
Studierendenticket,...). Heraus fällt pretix.csv

./convert.py

  IDs for FOSSGIS-Konferenzticket (diese aendern sich jedes Jahr und müssen angepasst werden)
  ids = [268184,268185,268218,268218,268218,270039,272120,272122,272123,271553]

3. namensschilder.pdf erzeugen
Als nächster Schritt muss mit pdflatex namensschilder.tex ein PDF mit
den Namensschildern erzeugt werden. 

Systemvoraussetzungen
sudo apt install texlive-latex-base
sudo apt install texlive-latex-extra
sudo apt-get install texlive-font-utils
sudo apt-get install texlive-fonts-extra

pdflatex namensschilder.tex

Anpassung der Datei namensschilder.tex:
Die Datei namensschilder.tex muss angepasst werden. Vor allem muss in der Zeile mit DTLforeach die
auszuwählenden Spaltennamen gesetzt werden (nickname auf die richtige Nr. setzen).
Damit die richtigen Grafiken verwendet werden, müssen diese unter imgs aktualisiert werden (fossgis-konferenz.png, skyline.pdf) 

 \DTLforeach{CSV}{\person=Name,\nickname=8835}

Aktuell wird pro Zeile der Name zwei mal ausgegeben, damit man das
Namensschild knicken kann und hinten und vorne beschriftet ist und man
in die Mitte noch Zusatzzettel (z.B. die Tokens für die Umfrage)
einlegen kann.

Achtung: Das lesen der CSV-Datei und Erstellen des PDFs dauert
lange. Zum schnelleren Testen sollte man sich daher eine
Test-CSV-Datei mit nur wenigen Zeilen zurecht legen.

Achtung: csv-Datei muss ggf. manuell angepasst werden (Sonderzeichen, falsche Angaben in Spalten). Außerdem sollte das Ergebnis geprüft werden (lange Namen).

Achtung: es sollten ein paar leere Einträge in die csv eingefügt werden. So können während der Konferenz noch Lanyards ausgegeben werden.


