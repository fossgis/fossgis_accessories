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

echo "Converting JSON to CSV"
python3 bin/convert2025.py

echo "create the PDFs in /pdf"
mkdir -p pdf

for badge_csv in csv/badges2025_*.csv; do
    if [ -f "$badge_csv" ]; then

        echo "Sanitize $badge_csv"
        sed -i 's/\"//g' "$badge_csv"

        echo "writing inner site of badges"
        jobname=$(basename -a $badge_csv)
        jobname="${jobname%.csv}"

        echo "Create ${jobname} PDFs"

        if [[ $badge_csv =~ .*(pseudo|conf|osm)\.csv$ ]]; then
          echo "mit Innenseite"
          BadgeInnenSeiten=True
        else
          echo "nur Aussenseiten"
          BadgeInnenSeiten=False
        fi
        pdflatex -jobname="pdf/${jobname}" \
                "\newcommand{\BadgeInnenSeiten}{$BadgeInnenSeiten}" \
                "\newcommand{\BadgeCSV}{$badge_csv}"  \
                "\input{tex/namensschilder2025.tex}"


          #echo "writing invisible site of badges"
          #pdflatex -jobname="pdf/${jobname}_innen" "\newcommand{\BadgeCSV}{$badge_csv} \input{tex/namensschilder_innen.tex}"
          #echo "writing visible site of badges"
          #pdflatex -jobname="pdf/${jobname}_aussen" "\newcommand{\BadgeCSV}{$badge_csv} \input{tex/namensschilder_sichtbar.tex}"

        #else
        #  echo "None"
        #  pdflatex -jobname="pdf/${jobname}" "\newcommand{\BadgeCSV}{$badge_csv} \input{tex/namensschilder_sichtbar.tex}"
        #fi


    fi
done

echo "Cleanup"
rm -f pdf/*.aux
rm -f pdf/*.log
rm -f pdf/*.out

#echo "combining in- and outside"
#pdflatex namensschilder2024.tex
# qpdf --empty --collate=1 --pages namensschilder2024_sichtbar.pdf namensschilder2024_innen.pdf -- out.pdf