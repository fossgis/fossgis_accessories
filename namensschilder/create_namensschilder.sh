#!/bin/bash

#  Diese Script erstellt ein A4 PDF
#  Ein A4 Blatt ergibt 4 Badge-Streifen.
#  Badge-Streifen = 2x A7 querformat zum zusammenklappen,
#  so das aussen das sichtbare Namensschild und innen ggf.nötige Zusatzinfos stehen
# 
#  1 PDF mit den A4 Vorderseiten (namensschilder_sichtbar.tex -> namensschilder_sichtbar.pdf)
#  2 PDF mit den A4 Innenseiten (namensschilder_innenseite.tex -> namensschilder_innenseite.pdf)
#  und fügt deren seiten abwechselnd zuammen zum namensschilder2024.pdf,
#  wo jede zweite 2 die Innenseite eines Badges darstellt
#  CSV = die *.csv datei mit den nötigen Angaben für Aussen- und Innenseite
# set CSV=bin/badges.empty.csv

export CSV=badges.D.csv # the real data
#export CSV=pseudodata.badges.D.csv # testdata
#export CSV="extra_badges.csv" # extrabadges
echo "CREATING BADGES for CSV: $CSV"

echo "Converting JSON to CSV"
python3 bin/convert2024.py

echo "Sanitize csv"
sed -i 's/\"//g' badges.D.csv

echo "writing inside of badges"
pdflatex namensschilder2024_innen.tex

echo "writing outside of badges"
pdflatex namensschilder2024_sichtbar.tex

echo "combining in- and outside"
pdflatex namensschilder2024.tex
# qpdf --empty --collate=1 --pages namensschilder2024_sichtbar.pdf namensschilder2024_innen.pdf -- out.pdf