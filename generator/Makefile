all:
	xelatex teilnehmerzettel.tex
	pdfnup --nup 2x4 --paper a4paper --no-landscape teilnehmerzettel.pdf


clean:
	rm images/*.pdf teilnehmerzettel.aux teilnehmerzettel.log \
	teilnehmerzettel.pdf teilnehmerzettel-nup.pdf \
	teilnehmer.csv teilnehmer.tex
