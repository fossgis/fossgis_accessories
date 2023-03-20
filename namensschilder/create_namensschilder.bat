:: Diese Script erstellt ein A4 PDF
:: Ein A4 Blatt ergibt 4 Badge-Streifen.
:: Badge-Streifen = 2x A7 querformat zum zusammenklappen,
:: so das aussen das sichtbare Namensschild und innen ggf.nötige Zusatzinfos stehen
::
:: 1 PDF mit den A4 Vorderseiten (namensschilder_sichtbar.tex -> namensschilder_sichtbar.pdf)
:: 2 PDF mit den A4 Innenseiten (namensschilder_innenseite.tex -> namensschilder_innenseite.pdf)
:: und fügt deren seiten abwechselnd zuammen zum namensschilder2023.pdf,
:: wo jede zweite 2 die Innenseite eines Badges darstellt
:: CSV = die *.csv datei mit den nötigen Angaben für Aussen- und Innenseite
::set CSV=bin/badges.empty.csv
set CSV=bin/pseudodata.badges.csv
set CSV=bin/badges.B.proof.csv
pdflatex "\newcommand{\BadgeCSV}{%CSV%} \input{namensschilder2023_innen.tex}"
pdflatex "\newcommand{\BadgeCSV}{%CSV%} \input{namensschilder2023_sichtbar.tex}"
pdflatex "\newcommand{\PDFSichtbar}{namensschilder_sichtbar.pdf} \newcommand{\PDFInnen}{namensschilder_innenseite.pdf} \input{namensschilder2023.tex}"