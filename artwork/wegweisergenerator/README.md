This is a collection of outdoor direction signs created for FOSSGIS 2017. These signs can be freely combined from building blocks using (svg_stack.py)[https://github.com/astraw/svg_stack].

Each sign needs to consist of a header element, three body elements (which can be Empty.svg) and the footer element.

The following are examples of actual FOSSGIS 2017 signs generated this way:

python svg_stack.py --direction=v SignHeader.svg AMdown.svg Mensaleft.svg IMright.svg SignFooter.svg 
  174  python svg_stack.py --direction=v SignHeader.svg AMdown.svg Mensaleft.svg IMright.svg SignFooter.svg > SignAMTreppe.svg
  175  python svg_stack.py --direction=v Header.svg AMdown.svg Mensadown.svg IMdown.svg Footer.svg > SignAMTreppe.svg
  176  python svg_stack.py --direction=v Header.svg AMdown.svg Mensaleft.svg IMright.svg Footer.svg > SignAMTreppe.svg
  180  python svg_stack.py --direction=v Header.svg AMleft.svg Mensaleft.svg IMright.svg Footer.svg > SignZugangTelefon.svg
  181  python svg_stack.py --direction=v Header.svg AMleft.svg Mensaleft.svg IMup.svg Footer.svg > SignJUR.svg
  182  python svg_stack.py --direction=v Header.svg Mensaright.svg Empty.svg Empty.svg Footer.svg > SignMensaFront.svg
  183  python svg_stack.py --direction=v Header.svg Mensaleft.svg AMup.svg IMup.svg Footer.svg > SignMensaBack.svg
  
The finished signs can also be found in the "complete" subfolder.

It's possible to convert the SVG files to PDF using inkscape on the command line. Example usage:

inkscape SignMensaBack.svg --export-pdf=SignMensaBack.pdf
