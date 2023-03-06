#!/usr/bin/python3
# -*- coding: utf-8 -*-
import collections
import csv
import json
import pathlib
import re
import sys
from typing import Dict, List

PATH_JSON = '2023_pretixdata.json'
PATH_BADGE_CSV = 'badges.csv'

PATH_JSON = pathlib.Path(PATH_JSON).resolve()
PATH_BADGE_CSV = pathlib.Path(PATH_BADGE_CSV).resolve()
PATH_ITEM_CSV = PATH_BADGE_CSV.parent / re.sub(r'\.csv$', '.Items.csv', PATH_BADGE_CSV.name)

CSV_LIMIT = -1
# Auflistung IDs für Workshop Tickets
#
# hier ggf. eine Liste mit order codes nutzen um nur selektiv badges zu erstellen
# ORDER_CODES = ['M7UNC', 'VXWKS']
ORDER_CODES = None

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


class BadgeInfo(object):
    """
    Alles Infos die in eine *.csv Zeile und mit einem Badge ausgedruckt werden sollen.
    """

    def __init__(self):
        self.order: str = None
        self.name: str = None
        self.nachname: str = None
        self.mail: str = None
        self.ticket: str = None
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


def extractSurname(name: str) -> str:
    name = normalize(name)
    split = name.split(" ")
    return split[-1]


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
        if status != 'p':  # p = payed, s = storniert
            # nur für bezahlte Orders erstellen
            continue

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
                    s = ""
                elif itemID == 73483:  # Ihre vollstÃ¤ndige Versandadresse fÃ¼r gedruckten Tagungsband:
                    s = ""
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
                    data[k] = f'\\\\ '.join(v)
            writer.writerow(data)

            cnt += 1


if __name__ == '__main__':
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

    # 3. schreibe badge CSV
    badges = readBadgeInfos(jsonData)
    writeBadgeCsv(badges, PATH_BADGE_CSV)
    print("\nNumber of attendees: " + str(len(badges)))
