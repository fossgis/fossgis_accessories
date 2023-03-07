#!/usr/bin/python3
# -*- coding: utf-8 -*-
import collections
import csv
import json
import pathlib
import random
import re
import sys
from typing import Dict, List

PATH_JSON = '2023_pretixdata.json'
PATH_BADGE_CSV = 'badges.csv'

# hier ggf. eine Liste mit order codes nutzen um selektiv badges zu erstellen
# https://pretix.eu/control/event/fossgis/2023/orders/<order code>/
# ORDER_CODES = ['M7UNC', 'VXWKS']
ORDER_CODES = None
# ORDER_CODES = ['WAPK9']

# if >0 -> beschränkt das aus der json generierte CSV auf CSV_LIMIT Zeilen.
# Gut um schnell zu testen ob das PDF sinnvoll aussieht
CSV_LIMIT: int = -1

# if True -> generiert ein Pseudo-CSV mit Max & Maria Musterfrau data
PSEUDODATA: bool = False

# Auflistung IDs für Workshop Tickets
#


TICKET_IDs = [
    272120,  # Konferenzticket Beitragende
    268184,  # Konferenzticket
    268185,  # Konferenzticket Community
    268218,  # Konferenzticket - reduzierter Preis
    270039,  # Konferenzticket fÃ¼r Helfende
]

# Workshop IDs
WORKSHOP_IDs = [
    270040,  # Punktwolkeverarbeitung und Analyse mit PDAL
    270041,  # QGIS 3 Workshop
    270042,  # MapProxy im Praxiseinsatz
    270043,  # QGIS-Pluginentwicklung mit Python
    270044,  # Hands on basemap.de
    270045,  # Die Open Database License (ODbL) der OpenStreetMap-Daten
    270046,  # PostgreSQL / PostGIS Workshop fÃ¼r Einsteiger
    270047,  # Orchestrierung einer GDI Ã¼ber Docker
    270048,  # Webmapping in nur 90 Minuten mit Leaflet
    270049,  # Masterportal in der Praxis
    270050,  # OberflÃ¤chenklassifikation aus Luft- und Satellitenbildern mit Hilfe von actinia
    270051,  # Geodateninfrastruktur mit Docker
    271541,  # Mobiles QGIS mit merginmaps
    271542,  # EinfÃ¼hrung GeoServer
    271543,  # Mapbender - Einstieg in den Aufbau von WebGIS-Anwendungen
    271544,  # Openstreetmap-Daten mit ogr2ogr und SQL fÃ¼r QGIS aufbereiten
    271545,  # QGIS 3D, LiDAR Punktwolken und Profilwerkzeug
    271546,  # Datenschutz und geographische Informationen
    271547,  # React basierte WebGIS Clients mit MapComponents & MapLibre-gl
    271548,  # Formulare gestalten in QGIS
    271550,  # GDI "instant"
    271551,  # Update your MapServer from 7 to 8
    282424,  # Nahtlose Feldarbeit dank QField und QFieldCloud
    272135,  # Workshopnachbuchung
]

EXKURSIONEN_IDs = [
    285619,  # Exkursion zur Kartensammlung der Staatsbibliothek zu Berlin (Freitag, 16:30 Uhr)
    296852,  # Exkursion zur Kartensammlung der Staatsbibliothek zu Berlin (Samstag, 10 Uhr)
    296853,  # Exkursion zur Campus Adlershof (Freitag, 16:30 Uhr)
]

# END SETTINGS

PATH_JSON = pathlib.Path(PATH_JSON).resolve()
PATH_BADGE_CSV = pathlib.Path(PATH_BADGE_CSV).resolve()
PATH_ITEM_CSV = PATH_BADGE_CSV.parent / re.sub(r'\.csv$', '.Items.csv', PATH_BADGE_CSV.name)


class BadgeInfo(object):
    """
    Alles Infos die in eine *.csv Zeile und mit einem Badge ausgedruckt werden sollen.
    """

    def __init__(self, name: str = None, company: str = None, mail: str = None, ticket: str = None, notes: str = None):
        self.order: str = None
        self.name: str = name
        self.nachname: str = extractSurname(name) if isinstance(name, str) else None
        self.company: str = company
        self.mail: str = mail
        self.ticket: str = ticket
        self.tl_name: str = None
        self.tl_veroeff: bool = False
        self.tl_erhalten: bool = False
        self.essen: str = None
        self.tshirt: str = None
        self.av: bool = False
        self.tb: bool = False
        self.tb_adresse: str = None
        self.osm_samstag: bool = False
        self.osm_name: str = True
        self.exkursionen: List[str] = []
        self.workshops: List[str] = []
        self.notes: str = notes  # sonstiges

    def __str__(self):
        return f'Ticket:#{self.order},{self.nachname},{self.name}'


class csvDialect(csv.Dialect):
    """Describe the usual properties of Unix-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL


def normalize(name: str) -> str:
    """

    :param name:
    :return:
    """
    name = name.replace(", BSc", "")
    if name.find(" (") > 0:
        name = name[:name.find(" (")]
    return name


# escape LaTeX characters
# credits to https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
conv = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\^{}',
    '\\': r'\textbackslash{}',
    '<': r'\textless{}',
    '>': r'\textgreater{}',
}
rx_tex_escape = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key=lambda item: - len(item))))


def tex_escape(text):
    """
    :param text: a plain text message
    :return: the message escaped to appear correctly in LaTeX
    """
    return rx_tex_escape.sub(lambda match: conv[match.group()], text)


def extractSurname(name: str) -> str:
    name = normalize(name)
    split = name.split(" ")
    return split[-1]


def extractFirstName(name: str) -> str:
    name = normalize(name)
    return name.split(' ')[0]


# print(json.dumps(data, indent=4))

def readEventItems(jsonData: dict) -> Dict[int, str]:
    """
    Liest alle Event Items ein
    :param jsonData:
    :return: dict
    """
    items = {}
    for item in jsonData["event"]["items"]:
        iid = item['id']
        iname = item['name']
        items[iid] = iname
        for var in item["variations"]:
            vid = var["id"]
            assert vid not in items
            items[vid] = f'{var["name"]}'

    items = collections.OrderedDict(sorted(items.items()))
    return items


def readEventQuestions(jsonData: dict) -> Dict[int, str]:
    questions = {}
    for question in jsonData['event']['questions']:
        qid = question['id']
        assert qid not in questions
        questions[qid] = question['question']

    return questions


def writeItems(items: Dict[int, str], path_csv: pathlib.Path):
    path_csv = pathlib.Path(path_csv)
    # print Items and write them into a CSV
    with open(path_csv, 'w', encoding='utf-8', newline='') as f:
        header = ['ItemID', 'Name']
        writer = csv.DictWriter(f, header)
        writer.writeheader()
        for key, value in items.items():
            writer.writerow(dict(ItemID=key, Name=value))


def readPseudoBadgeInfos() -> Dict[str, BadgeInfo]:
    names = ['Max Mustermann', 'Maria Musterfrau',
             'Max Power', 'Wiener Schnitzel mit Kartoffelsalat',
             'Erwin Gerwin', 'Arne-Unhold Obermeier']
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    workshops = ['Workshop 1',
                 'Workshop 2 mit langen Namen ärgerlichen Sonderzeichen',
                 'Workshop 3 mit äußerst langem Namen und CSV zerstörenden ;:,\t Zeichen']

    exkursionen = ['Exkursion 1',
                   'Exkursion 2 mit langen Namen ärgerlichen Sonderzeichen',
                   'Exkursion 3 mit äußerst langem Namen und CSV zerstörenden ;:,\t Zeichen']

    tickets = ['Konferenzticket Beitragende', 'Konferenzticket Community', 'Konferenzticket - reduzierter Preis',
               'Konferenzticket fÃ¼r Helfende']

    essen = ['Vegan', 'Vegetarisch', 'Fleisch/Fisch']

    companies = ['Humboldt-Universität zu Berlin', 'Firma A GmbH', 'Bundesamt für XY und Z', 'Obelix GmbH & Co KG']

    notes = ['<weitere Anmerkungen>', '<andere Anmerkungen>']
    tshirts = []
    for schnitt in ['tailliert geschnitten', 'gerade geschnitten']:
        for size in ['M', 'L', 'XL', '2XL', '3XL']:
            tshirts.append(f'{schnitt} - {size}')

    BADGES = {}

    def rnd(options: List, multiple: bool = False):
        if random.choice([True, False]):
            if multiple:
                return random.sample(options, random.choice(range(len(options))))
            else:
                return random.choice(options)

        else:
            return None

    for name in names:
        badge = BadgeInfo()
        badge.name = name
        badge.order = ''.join(random.sample(letters, 5))
        badge.nachname = extractSurname(name)
        badge.tshirt = rnd(tshirts)
        badge.ticket = random.choice(tickets)
        badge.av = random.choice([True, False])
        badge.tb = random.choice([True, False])
        badge.tb_adresse = f'Pseudo Adresses {badge.name}'
        badge.osm_samstag = random.choice([True, False])
        badge.osm_name = extractFirstName(name).lower()
        badge.mail = f'{badge.osm_name}{badge.nachname.lower()}@nomail.xyz'
        badge.workshops = rnd(workshops, multiple=True)
        badge.exkursionen = rnd(exkursionen, multiple=True)
        badge.essen = rnd(essen)
        badge.notes = rnd(notes)
        badge.company = rnd(companies)
        BADGES[name] = badge
    return BADGES


def readBadgeInfos(jsonData: dict) -> Dict[str, BadgeInfo]:
    BADGES = {}

    ITEMS = readEventItems(jsonData)
    QUESTIONS = readEventQuestions(jsonData)

    ORDERS_TO_CHECK: Dict[str, str] = {}

    for cntOrder, order in enumerate(jsonData["event"]["orders"]):
        # !eine Order kann mehrere Tickets enthalten
        # !eine Order kann nur Online Tickets enthalten und wie brauchen wir hier nicht

        orderCode = order['code']  # z.B. "LSVKC"
        status = order['status']
        # p = payed, s = storniert, n = nicht bezahlt, c = canceled
        if status in ['s', 'c']:
            continue
        assert status in ['p', 'n'], f'unhandled status {status}'

        if isinstance(ORDER_CODES, list) and orderCode not in ORDER_CODES:
            continue

        badge: BadgeInfo = None
        for cntPos, pos in enumerate(order["positions"]):
            itemID = pos['item']
            variationID = pos['variation']
            itemName = ITEMS[itemID]
            variationName = ITEMS[variationID] if variationID else itemName
            questions = {qa['question']: qa['answer'] for qa in pos['answers']}

            name = pos['attendee_name']
            mail = pos['attendee_email']
            if name:
                badge = None
            if itemID in TICKET_IDs:
                badge = BadgeInfo()
                badge.order = orderCode
                if name in BADGES:
                    existingTicket = BADGES[name]
                    ORDERS_TO_CHECK[orderCode] = f'{name}:Ticket existiert bereits {existingTicket.order}'
                    continue
                badge.mail = mail
                badge.name = questions.get(69219, name)  # 1. Name für Teilnehmerliste, 2. Bestellungs Name
                badge.nachname = extractSurname(name)
                BADGES[name] = badge
                badge.ticket = variationName

                for qid, qanswer in questions.items():
                    qname = QUESTIONS[qid]
                    if qid in [69296,  # Ich helfe...
                               69291,  # Ich bin...
                               69295,  # In dr FOSSGIS-Community bin ich aktiv ...
                               69293,  # Wo liegt dein Sourcecode?
                               ]:
                        continue
                    elif qid == 69219:  # Name Teilnehmerliste
                        badge.tl_name = qanswer
                    elif qid == 69290:  # Ich mÃ¶chte meinen Namen und meine Email-Adresse in der Teilnehmer:innenliste verÃ¶ffentlichen.
                        badge.tl_veroeff = str(qanswer).lower() in ['true']
                    elif qid == 69294:  # Name Englesystem
                        badge.engel = qanswer
                    elif qid == 69292:  # Wie is dein Mappername?
                        badge.osm_name = qanswer
                    else:
                        s = ""
                    del qid, qname, qanswer
            else:
                if badge is None:
                    s = ""
                    continue
                if itemID == 271559:  # T-Shirt
                    badge.tshirt = variationName
                elif itemID == 274775:  # Helfer T-Shirt:
                    badge.tshirt = variationName
                elif itemID == 271557:  # Ich möchte einen Tagungsband erhalten
                    badge.tb = True
                elif itemID == 73483:  # Ihre vollstÃ¤ndige Versandadresse fÃ¼r gedruckten Tagungsband:
                    badge.tb_adresse = ''
                elif itemID == 271558:  # Ich möchte eine Teilnehmer:innenliste erhalten
                    badge.tl_erhalten = True
                elif itemID in [274773, 281276, 275242]:  # Mittagessen
                    badge.essen = variationName
                elif itemID == 271556:  # Ja, ich nehme an der Abendveranstaltung teil.
                    badge.av = True
                elif itemID in EXKURSIONEN_IDs:
                    badge.exkursionen.append(variationName)
                elif itemID in WORKSHOP_IDs:
                    badge.workshops.append(variationName)
                elif itemID == 271553:  # OSM-Samstag
                    badge.osm_samstag = True
                else:
                    s = ""
            s = ""

    if len(ORDERS_TO_CHECK) > 0:
        print('Überprüfen:')
        for k, v in ORDERS_TO_CHECK.items():
            print(f'{k}: {v}', file=sys.stderr)
    return BADGES


def writeBadgeCsv(badgeInfos: Dict[str, BadgeInfo], path_csv: pathlib.Path):
    path_csv = pathlib.Path(path_csv)

    badgeInfos = sorted([p for p in badgeInfos.values()], key=lambda p: p.nachname)
    with open(path_csv, 'w', encoding='utf-8', newline='') as f:

        # schreibe alle Attribute als CSV Spalte
        p = badgeInfos[0]
        header = [k for k in p.__dict__.keys() if not k.startswith('_')]

        writer = csv.DictWriter(f, header, dialect=csvDialect)
        writer.writeheader()

        cnt = 0
        for person in badgeInfos:
            if CSV_LIMIT > 0 and cnt >= CSV_LIMIT:
                break
            data = {k: person.__dict__[k] for k in header}
            for k in list(data.keys()):
                v = data[k]
                if isinstance(v, list):
                    latex = f'{len(v)}'
                    if len(v) > 0:
                        v = [tex_escape(line) for line in v]
                        if False:
                            latex += r'\\ -- ' + r' \\ -- '.join(v)
                        else:
                            # geht leider nicht, weil
                            latex += r' \begin{itemize} '
                            latex += r' \item ' + r' \item '.join(v)
                            latex += r' \end{itemize}\leavevmode '
                    v = latex
                elif isinstance(v, str):
                    v = tex_escape(v)
                if k == 'name':
                    # Füge bei sehr langen Namen ein Leerzeichen ein
                    # damit auf dem Badge ein Zeilenumbruch entsteht
                    parts = re.split(r'[ ]+', v)
                    for i in range(len(parts)):
                        part = parts[i]
                        if len(part) > 20:
                            parts[i] = re.sub('-', '- ', part)
                    v = ' '.join(parts)
                data[k] = v
            writer.writerow(data)

            cnt += 1


if __name__ == '__main__':

    if PSEUDODATA:
        print('Create Badges with Pseudo-Data')
        badges = readPseudoBadgeInfos()
    else:
        # 1. lese JSON
        with open(PATH_JSON, 'r', encoding='utf-8') as f:
            jsonData = json.load(f)

        # 2. lese &  schreibe items + variations aka Dinge die gebucht werden können
        items = readEventItems(jsonData)
        questions = readEventQuestions(jsonData)
        print("Items:")
        for key, value in items.items():
            print(f'{key}, # {value}')
        writeItems(items, PATH_ITEM_CSV)

        print('\nQuestions:')
        for key, value in questions.items():
            print(f'{key}, #{value}')

        # 3. Lese Badge Data
        badges = readBadgeInfos(jsonData)
    # 4. Schreibe badge CSV

    writeBadgeCsv(badges, PATH_BADGE_CSV)
    print("\nNumber of attendees: " + str(len(badges)))
