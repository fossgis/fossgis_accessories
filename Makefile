all:
	./generate-teilnehmer
	xelatex teilnehmerzettel.tex
	pdfnup --nup 1x4 --paper a4 --no-landscape teilnehmerzettel.pdf


clean:
	rm images/*.pdf teilnehmerzettel.aux teilnehmerzettel.log \
	teilnehmerzettel.pdf teilnehmerzettel-nup.pdf \
	teilnehmer.csv teilnehmer.tex
