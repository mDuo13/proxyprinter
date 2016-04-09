Proxy Printer
=============

Generates reasonbly good-looking proxies for a card game from an ODS spreadsheet. Useful for making card game prototypes. Comes with some basic CSS; you can add your own style rules to make the proxies prettier or better suited to your game. Does some heuristic text resizing so that text of different lengths is more likely to fit without being too small.


Setup
------

* Python 3 required
* Install [pyexcel-ods3](https://github.com/pyexcel/pyexcel-ods3)

Usage
------

     ./proxyprinter.py cards.ods > output_file.html

Do `./proxyprinter.py --help` for usage statement with all commandline options.


Input Format
-------------
OpenDocument Spreadsheet (ODF) file. Example: [cards.ods](cards.ods). Each "Sheet" in the document is one type of card in your game. The name of the sheet is the card type. The first row in the sheet lists the titles for each field. Each subsequent row is a card.

The following field names are special in some way:

- **Name**: The name of your card (goes in the title area of the card).
- **Traits**: A comma-separated list of tags/labels for the card. Each gets its own span with a class so you can style it.
- **Text**: Gets put in a single text_area alongside Flavor Text.
- **Flavor Text**: Gets put in a single text_area alongside Text.
- **Version**: Listed in the footer. Use this with the `-v` switch to only print recently-updated cards.
