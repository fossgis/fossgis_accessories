:: diese script erstellt die A4 Badge Blätter vorder (namensschilder_innenseite.tex -> pdf) und
:: Rückseiten (namensschilder_innenseite.tex -> pdf)
:: CSV -> die CSV datei mit ggf. manuell korrigierten Namen

set CSV=bin/fehlende_badges.C.2.csv
pdflatex "\newcommand{\BadgeCSV}{%CSV%} \input{namensschilder_innenseite.tex}"
pdflatex "\newcommand{\BadgeCSV}{%CSV%} \input{namensschilder_sichtbar.tex}"