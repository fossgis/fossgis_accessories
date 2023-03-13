import csv
import json
import pathlib
import re
from typing import Dict, List
from convert2023 import TICKET_IDs, tex_escape

PATH_JSON = '2023_pretixdata.json'  # Bestelldaten
PATH_NREI = '2023_nrei.json'  # 'Rechnungsdaten -> für Firmennamen
PATH_CSV = 'workshopliste.csv'

PATH_CSV = pathlib.Path(PATH_CSV).resolve()


class csvDialect(csv.Dialect):
    """Describe the usual properties of Unix-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL


# WS-Raum 1 Spreewald (1'231): 24 Plätze "Spreewald (1'231)"
# WS-Raum 2 Teltow (1'101): 16 Plätze
# WS-Raum 3 Prignitz (1'230): 12 Plätze
class RAUEME(object):
    Spreewald24 = "Spreewald (1'231) 24 Pätze"
    Teltow16 = "Teltow (1'101) 16 Plätze"
    Prignitz12 = "Prignitz (1'230): 12 Plätze"


# Ordnet Räume einzelnen Workshops zu
WS_RAEUME = {
    'Punktwolkeverarbeitung und Analyse mit PDAL': RAUEME.Spreewald24,
    "QGIS 3 Workshop": RAUEME.Prignitz12,
    "MapProxy im Praxiseinsatz": RAUEME.Teltow16,
    "QGIS-Pluginentwicklung mit Python": RAUEME.Spreewald24,
    "Hands on basemap.de": RAUEME.Teltow16,
    "PostgreSQL / PostGIS Workshop für Einsteiger": RAUEME.Spreewald24,
    "Orchestrierung einer GDI über Docker": RAUEME.Teltow16,
    "Webmapping in nur 90 Minuten mit Leaflet": RAUEME.Prignitz12,
    "Masterportal in der Praxis": RAUEME.Spreewald24,
    "Geodateninfrastruktur mit Docker": RAUEME.Prignitz12,
    "QGIS 3D, LiDAR Punktwolken und Profilwerkzeug": RAUEME.Teltow16,
    "Mobiles QGIS mit merginmaps": RAUEME.Spreewald24,
    "Einführung GeoServer": RAUEME.Teltow16,
    "Mapbender - Einstieg in den Aufbau von WebGIS-Anwendungen": RAUEME.Prignitz12,
    "Oberflächenklassifikation aus Luft- und Satellitenbildern mit Hilfe von actinia": RAUEME.Teltow16,
    "Openstreetmap-Daten mit ogr2ogr und SQL für QGIS aufbereiten": RAUEME.Spreewald24,
    "Datenschutz und geographische Informationen": RAUEME.Prignitz12,
    "React basierte WebGIS Clients mit MapComponents & MapLibre-gl": RAUEME.Spreewald24,
    "Nahtlose Feldarbeit dank QField und QFieldCloud": RAUEME.Teltow16,
    "Formulare gestalten in QGIS": RAUEME.Spreewald24,
    "Update your MapServer from 7 to 8": RAUEME.Prignitz12,
}


class Teilnehmer(object):

    def __init__(self):
        self.name: str = None
        self.mail: str = None
        self.order: str = None


class Workshop(object):

    def __init__(self):
        self.name: str = None
        self.itemId: int = None
        self.description: str = None
        self.leitung: str = None
        self.zeit: str = None
        self.raum: str = None
        self.teilnehmer: List[str] = []

    def __str__(self):
        return f'Workshop: {self.zeit}:{self.leitung}:{self.name}'


rx_ws = re.compile('Workshop[ ]+(?P<datetime>.*)')


def readTicketItemsFromOrder(order) -> List[Dict]:
    items = []
    for pos in order['positions']:
        if pos['item'] in TICKET_IDs:
            items.append(pos)
    return items


def readWorkshops(jsonData: Dict) -> Dict[str, dict]:
    workshops = {}

    wsTime = {}

    for cat in jsonData['event']['categories']:
        name = cat['name']
        match = rx_ws.match(name)
        if match:
            wsTime[cat['id']] = match.group('datetime')
        s = ""

    for item in jsonData["event"]["items"]:
        if re.search('Workshopleitung', item['description'], re.I):
            ws = Workshop()
            ws.itemId = item['id']
            name = item['name']
            ws.raum = WS_RAEUME.get(name, None)
            ws.name = tex_escape(name)
            html = item['description']
            parts = [s.strip() for s in re.split('<[^>]+>', html)]
            parts = [tex_escape(s) for s in parts if len(s) > 0]
            ws.leitung = parts[1]
            ws.description = parts[3]
            ws.zeit = wsTime[item['category']]
            workshops[ws.itemId] = ws

    ORDERS = {o['code']: o for o in jsonData['event']['orders']}

    for order in ORDERS.values():
        if order['status'] in ['c', 's']:
            continue
        code = order['code']

        for i, item in enumerate(order['positions']):
            itemID = item['item']
            if itemID in workshops:
                ws = workshops[itemID]
                # got back to find the attendee_name
                for j in reversed(range(i)):
                    pos = order['positions'][j]

                    if pos['attendee_name']:
                        tn = Teilnehmer()
                        tn.name = pos['attendee_name']
                        tn.order = code
                        tn.mail = pos['attendee_email']
                        ws.teilnehmer.append(tn)
                        break
                    elif pos['item'] == 272135:  # Workshopnachbuchung - diese können wir nicht mehr eindeutig
                        # einem User zuordnen
                        answers = {a['question']: a['answer'] for a in pos['answers']}
                        refCode = answers[69297]
                        # existiert die Reference order
                        if len(refCode) > 5:
                            match = re.search('[A-Z0-9]{5}', refCode)
                            if match:
                                refCode = match.group()
                        if refCode in ORDERS:
                            refOrder = ORDERS[refCode]
                            refTickets = readTicketItemsFromOrder(refOrder)
                            tn = Teilnehmer()
                            if len(refTickets) == 1:
                                tn.mail = refTickets[0]['attendee_email']
                                tn.name = refTickets[0]['attendee_name']
                            else:

                                tn.mail = order['email']
                                tn.name = '<Nachbuchung>'
                            tn.order = f'{code}->{refCode}'

                            ws.teilnehmer.append(tn)
                        else:
                            s = ""
                    elif j == 0:
                        s = ""

                s = ""

    return workshops


def writeWorkshops(workshops: List[Workshop], path_csv: pathlib.Path):
    assert isinstance(path_csv, pathlib.Path)
    tex_lines = []
    csv_lines = []
    path_tex = path_csv.parent / re.sub(r'\.csv$', '.tex', path_csv.name)
    header = ['ws', 'wsname', 'wszeit', 'wsraum', 't', 'tname', 'tmail', 'torder']

    workshops = [w for w in workshops if len(w.teilnehmer) > 0]

    with open(path_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, header, dialect=csvDialect)
        writer.writeheader()

        for i, ws in enumerate(workshops):
            for j, tn in enumerate(ws.teilnehmer):
                tn: Teilnehmer
                row = dict(ws=i + 1,
                           wsname=ws.name,
                           wszeit=ws.zeit,
                           wsraum=ws.raum,
                           t=j + 1,
                           torder=tn.order,
                           tname=tn.name,
                           tmail=tn.mail,
                           )
                writer.writerow(row)

    tex_lines = [r'\begin{landscape}']


    tex_lines.append(f"""
    \centering
    \LARGE FOSSGIS 2023 Workshops
    \\normalsize
    """)
    tex_lines.append(r'\begin{tabularx}{\columnwidth}{l|l|p{3cm}|l}'
                     r'Zeit & Raum & Leitung & Workshop \\'
                     r'\hline')
    rx_raum = re.compile(r'(?P<name>.+) \((?P<raum>.*)\).*')
    for i, ws in enumerate(workshops):
        zeit = ws.zeit.replace('Mittwoch', 'Mi')
        for k, v in {'Mittwoch': 'Mi', 'Donnerstag': 'Do', 'Freitag': 'Fr'}.items():
            zeit = zeit.replace(k, v)
        if ws.raum:
            match = rx_raum.match(ws.raum)
            raum = '{} {}'.format(match.group('raum'), match.group('name'))
        else:
            raum = None
        tex_lines.append(f'{zeit} & {raum} & {ws.leitung} & {ws.name} \\\\')
    tex_lines.append(r'\hline \end{tabularx} \end{landscape} \pagebreak')


    tex_lines.append(r'\renewcommand{\arraystretch}{2}')
    for i, ws in enumerate(workshops):
        if i > 0:
            tex_lines.append('\pagebreak')

        # tex_lines.append(r'\put(0,0){\includegraphics[width=25mm]{../imgs/2023/FOSSGIS_2023.pdf}}')

        # tex_lines.append(r'\raggedright \includegraphics[width=25mm]{../imgs/2023/FOSSGIS_2023.pdf}')
        tex_lines.append(

            f"""
            
            \centering 
            \Large FOSSGIS 2023 Workshop \par 
            \LARGE "{ws.name}" \par
            \large Leitung: {ws.leitung} \par
                   Zeit: {ws.zeit} \par
                   Raum: {ws.raum} \par
            """)
        tex_lines.append(r'Beschreibung: \par ' + ws.description + r' \par ')
        tex_lines.append(r'\vspace{1cm}')

        tex_lines.append(r'Teilnehmer:innen: \par \par \small')
        tex_lines.append(r'\begin{tabularx}{\columnwidth}{l|l|l|l|X} '
                         # r'\hline'
                         r'No. & Name & Mail & Order & Unterschrift \\ '
                         r'\hline ')
        teilnehmer = sorted(ws.teilnehmer, key=lambda tn: tn.name)
        for j, tn in enumerate(teilnehmer):
            cols = [j + 1, tn.name, tex_escape(tn.mail), tn.order]
            cols = ' & '.join([str(c) for c in cols]) + r' \\ '
            tex_lines.append(cols)
        tex_lines.append(r'\hline '
                         r'\end{tabularx} \vspace{\fill}' )

    with open(path_tex, 'w', encoding='utf-8') as f:
        f.writelines('\n'.join(tex_lines))


if __name__ == '__main__':
    # 1. lese JSON und Workshopdata
    with open(PATH_JSON, 'r', encoding='utf-8') as f:
        jsonData = json.load(f)
    workshops = readWorkshops(jsonData)

    # 2. Schreibe bin/workshopliste.csv und
    #             bin/workshopliste.tex -> wird von workshopliste.tex eingebunden
    writeWorkshops(workshops.values(), PATH_CSV)
