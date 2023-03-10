import csv
import json
import re
from typing import Dict, List

PATH_JSON = '2023_pretixdata.json' # Bestelldaten
PATH_NREI = '2023_nrei.json' # 'Rechnungsdaten -> für Firmennamen
PATH_CSV = 'workshopliste.csv'
class csvDialect(csv.Dialect):
    """Describe the usual properties of Unix-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL

class Workshop(object):

    def __init__(self):

        self.name = None
        self.description = None
        self.leitung = None
        self.uhrzeit = None
        self.tag = None

def readWorkshops(jsonData:Dict)->Dict[str, dict]:

    workshops = {}

    for cat in jsonData["event"]["items"]:
        if re.search('Workshopleitung', re.I, cat['description']):
            ws = Workshop()
            ws.id = cat['id']
            ws.name = cat['name']
            html = cat['description']
            ws.description = html
        workshops[ws.id] = ws
    for item in jsonData["event"]["items"]:
        s = ""

    return workshops
    pass

def writeWorkshops(workshops:List[Workshop], path):

    pass
if __name__ == '__main__':
    # 1. lese JSON
    with open(PATH_JSON, 'r', encoding='utf-8') as f:
        jsonData = json.load(f)
    workshops = readWorkshops(jsonData)

    writeWorkshops(workshops, PATH_CSV)