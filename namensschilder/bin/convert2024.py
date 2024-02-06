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

PATH_JSON = './bin/2024_pretixdata.json'  # Bestelldaten
PATH_NREI = './bin/2024_nrei.json'  # 'Rechnungsdaten -> für Firmennamen
PATH_ITEMS = './data/items.json'  # Produktdaten
PATH_BADGE_CSV = 'badges.D.csv'

# if True -> generiert ein pseudodata.badges.csv mit Max & Maria Musterfrau data
PSEUDODATA: bool = False

# hier ggf. eine Liste mit order codes nutzen um selektiv badges zu erstellen
# https://pretix.eu/control/event/fossgis/2023/orders/<order code>/
#
ORDER_CODES = None
# ORDER_CODES = ['PCJ7N']

# if >0 -> beschränkt das aus der json generierte CSV auf CSV_LIMIT Zeilen.
# Gut um schnell zu testen ob das PDF sinnvoll aussieht
CSV_LIMIT: int = -1

# Auflistung IDs für Workshop Tickets
#


TICKET_IDs = [
    416723,  # Konferenzticket
    416724,  # Konferenzticket - reduzierter Preis
    416725,  # Konferenzticket Community
    416726,  # Konferenzticket Beitragende x
    416727,  # Konferenzticket Aussteller
    416728,  # Konferenzticket fÃ¼r Helfende
    416739,  # OSM-Samstag
]

# Workshop IDs
WORKSHOP_IDs = [
    451468, # PostgreSQL / PostGIS Workshop für Einsteiger
    451473, # QGIS Workshop
    451477, # Orchestrierung einer GDI über Container Images
    416762, # QGIS-Programmierung ohne Python-Vorkenntnisse
    453049, # Einführung GeoServer
    454304, # Geodaten Prozessieren mit GeoPandas
    454307, # Nahtlose Feldarbeit dank QField und QFieldCloud
    454308, # Webmapping und Geoverarbeitung: Turf.js
    454330, # Oberflächenklassifikation aus Luft- und Satellitenbildern mit Hilfe von actinia
    454337, # Webmapping mit Leaflet - in nur 90 Minuten!
    454338, # MapProxy im Praxiseinsatz
    454344, # Labeling mit QGIS
    454350, # Hands on Masterportal
    454353, # Datenschutz und geographische Informationen
    454358, # Mapbender Workshop mit Schwerpunkt auf Mapbender 4
    454364, # QGIS Expressions Workshop: Overlay und Aggregate Funktionen nutzen
    454366, # Vom Desktop-GIS zum WebGIS - mit MapComponents und React
    454367, # Kartendrucke in QGIS mit Python automatisieren
    454368, # Die Open Database License (ODbL) der OpenStreetMap-Daten
    454369, # Keine Angst vor sperrigen Ausdrücken im QGIS: Der Workshop zur LiveDemo
    454370, # QGIS Beziehungen (Relationen) und ihre Widgets
]

EXKURSIONEN_IDs = [
    458277,  # Exkursion Blankenese – Altes Land – Finkenwerder – Landungsbrücken (Dienstag, 14:45 Uhr)
    454377,  # Einblick in die Kartensammlung der Staats- und Universitätsbibliothek Hamburg (Donnerstag, 9 Uhr)
    416720,  # Exkursion Hamburger Unterwelten (Freitag, 18:00 Uhr)
    458278,  # Exkursion Abendliche Hafenrundfahrt (Freitag, 17:45 Uhr)
    454378,  # MILLERNTOUR! Stadionführung bei St. Pauli (Samstag, 14:00 Uhr)
    458279,  # Exkursion – Stadtrundgang (Samstag, 09:15 Uhr)
]

# Hier können typos korrigiert, Firmennamen gekürzt und vereinheitlicht werden
DELETE_FROM_NAMES = [
    re.compile(r'FD Vermesssung und Geodaten Stadt Hildesheim[ ]*'),
    re.compile(r'Software Development[ ]*'),
    re.compile(r'Web GIS Freelance[ ]*'),
    re.compile(r'.* Consultants[ ]*'),
    re.compile(r'.* GmbH[ ]*'),
    re.compile(r'FH Aachen[ ]*'),
    re.compile(r'NTI Deutschland.*'),
]
REPLACE_IN_COMPANIES = {
    'Bundesamt für Kartographie und Geodäsie': re.compile('(BKG|Bundesamt für Kartographie und Geodäsie)'),
    'WhereGroup GmbH': re.compile(r'WhereGrouo?p GmbH', re.I),
    'DB Systel GmbH': re.compile('DB Systel GmbH c/o Deutsche Bahn AG'),
    'Landesamt für Geoinformation und Landesvermessung Niedersachsen': re.compile(
        r'LGLN|Landesamt für Geoinformation und Landesvermessung Niedersachsen', re.I),
    'Landesamt für Vermessung und Geobasisinformation Rheinland-Pfalz': re.compile(
        r'Landesamt für Vermessung und Geobasisinformation Rheinland-Pfalz', re.I),
    'Landesamt für Geoinformation und Landentwicklung Baden-Württemberg':
        re.compile(r'Landesamt für Geoinformation und Landentwicklung (Baden-Württemberg|BW)', re.I),
    'Landesvermessung und Geobasisinformation Brandenburg': re.compile('^LGB$'),
    'Staatsbibliothek zu Berlin': re.compile(r'staatsbibliothek zu berlin', re.I),
    'Umweltbundesamt (UBA)': re.compile(r'umweltbundesamt|\(UBA\)', re.I),
    'Stadt Leipzig': re.compile(r'Stadt Leipzig', re.I),
    'Technische Universität Chemnitz': re.compile('Technische Universität Chemnitz'),
    'Bezirksamt Tempelhof-Schöneberg von Berlin': re.compile(r'Bezirksamt Tempelhof-Schöneberg von Berlin', re.I),
    'DB Fahrwegdienste GmbH': re.compile(r'DB Fahrwegdienste GmbH', re.I),
    'Landesamt für Geoinformation \& Landesvermessung Niedersachsen': re.compile('LGLN'),
    'Leibniz-Zentrum für Agrarlandschaftsforschung (ZALF)': re.compile('ZALF'),
    'Deutsches Zentrum für Luft- und Raumfahrt (DLR)': re.compile('Deutsches Zentrum für Luft- und Raumfahrt'),
}

# END SETTINGS

PATH_JSON = pathlib.Path(PATH_JSON).resolve()
PATH_NREI = pathlib.Path(PATH_NREI).resolve()
PATH_ITEMS = pathlib.Path(PATH_ITEMS).resolve()
PATH_BADGE_CSV = pathlib.Path(PATH_BADGE_CSV).resolve()
PATH_ITEM_CSV = PATH_BADGE_CSV.parent / re.sub(r'\.csv$', '.Items.csv', PATH_BADGE_CSV.name)


class BadgeInfo(object):
    """
    Alles Infos die in eine *.csv Zeile und mit einem Badge ausgedruckt werden sollen.
    """

    def __init__(self,
                 name: str = None,
                 company: str = None,
                 mail: str = None,
                 orderCode: str = None,
                 ticket: str = None,
                 notes: str = None):
        self.order: str = orderCode
        self.name: str = normalizeName(name) if isinstance(name, str) else None
        self.nachname: str = extractSurname(self.name) if isinstance(self.name, str) else None
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
        self.osm_name: str = None
        self.exkursionen: List[str] = []
        self.workshops: List[str] = []
        self.notes: str = notes  # sonstiges
        self.nickname: str = None


    def id(self) -> str:
        return f'{self.name}:{self.mail}'

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


def normalizeName(name: str) -> str:
    """

    :param name:
    :return:
    """
    name = name.replace(", BSc", "")
    if name.find(" (") > 0:
        name = name[:name.find(" (")]
    name = re.sub(r'Dipl\.-(Ing|Geogr|Geol)\.[ ]+]', '', name)
    name = re.sub(
        r'(FD Vermesssung und Geodaten Stadt Hildesheim|Staatsbibliothek zu Berlin|Development and Operations| / Sourcepole)[ ]*',
        '', name)
    if ',' in name:
        name = ' '.join(reversed(re.split(r'[ ]*,[ ]*', name)))
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


def readCompanyNames(path: pathlib.Path) -> Dict[str, str]:
    CN = {}
    with open(path, 'r', encoding='utf-8') as f:
        jsonData = json.load(f)

    for data in jsonData['Data']:
        orderCode = data['Hdr']['OID']
        company = data['Hdr']['CN']
        CN[orderCode] = company

    return CN


def replace_strings(text: str, replacements: dict):
    for newtext, oldtext in replacements.items():
        if isinstance(oldtext, str):
            text = text.replace(oldtext, newtext)
        if oldtext.search(text):
            return newtext
    return text


def extractSurname(name: str) -> str:
    name = normalizeName(name)
    split = name.split(" ")
    return split[-1]


def extractFirstName(name: str) -> str:
    name = normalizeName(name)
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

    companies = ['Firma In-der-Kürze-liegt die Würze GmbH mit dennoch langem Namen', 'Bundesamt für XY und Z',
                 'Obelix GmbH & Co KG']

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
        badge.company = random.choice(companies)
        badge.nickname = nickname
        BADGES[name] = badge
    return BADGES


def readBadgeInfos(jsonData: dict, companyNames: Dict[str, str] = None) -> Dict[str, BadgeInfo]:
    BADGES: Dict[str, BadgeInfo] = {}

    ITEMS = readEventItems(jsonData)
    QUESTIONS = readEventQuestions(jsonData)

    ORDERS_TO_CHECK: Dict[str, str] = {}

    # p = payed, s = storniert, n = nicht bezahlt, c = canceled
    orders = [o for o in jsonData["event"]["orders"] if o['status'] not in ['s', 'c']]

    # 1. Create Badge for each ticket order
    for o in orders:
        code = o['code']
        if isinstance(ORDER_CODES, list) and code not in ORDER_CODES:
            continue
        for pos in o['positions']:
            mail = pos['attendee_email']
            name = pos['attendee_name']
            questions = {qa['question']: qa['answer'] for qa in pos['answers']}
            if pos['item'] in TICKET_IDs and isinstance(mail, str):
                cn = CompanyNames.get(code, None)
                if isinstance(cn, str):
                    cn = re.split(r'(, | \\ )', cn)[0]
                badge = BadgeInfo(mail=mail,
                                  name=questions.get(69219, name),
                                  orderCode=code,
                                  company=cn)
                BADGES[badge.id()] = badge

    for cntOrder, order in enumerate(jsonData["event"]["orders"]):
        # !eine Order kann mehrere Tickets enthalten
        # !eine Order kann nur Online Tickets enthalten und wie brauchen wir hier nicht

        code = order['code']  # z.B. "LSVKC"
        if isinstance(ORDER_CODES, list) and code not in ORDER_CODES:
            continue
        status = order['status']
        # p = payed, s = storniert, n = nicht bezahlt, c = canceled
        if status in ['s', 'c']:
            continue
        assert status in ['p', 'n'], f'unhandled status {status}'

        badge: BadgeInfo = None
        for cntPos, pos in enumerate(order["positions"]):
            itemID = pos['item']
            itemName = ITEMS[itemID]

            if itemID in [
                416717,  # Online - Konferenzticket - reduzierter Preis
                416718,  # Online - Konferenzticket Community
                416716,  # Online - Konferenzticket
            ]:
                badge = None
                continue
            elif itemID in TICKET_IDs:
                mail = pos['attendee_email']
                name = pos['attendee_name']
                badgeID = f'{name}:{mail}'
                if badgeID in BADGES:
                    badge = BADGES[badgeID]
                    if badge.ticket is None:
                        badge.ticket = itemName
                else:
                    s = ""
            if not isinstance(badge, BadgeInfo):
                continue

            itemID = pos['item']
            variationID = pos['variation']
            itemName = ITEMS[itemID]
            variationName = ITEMS[variationID] if variationID else itemName

            # read questions
            questions = {qa['question']: qa['answer'] for qa in pos['answers']}

            for qid, qanswer in questions.items():
                qname = QUESTIONS[qid]

                if qid in [69296,  # Ich helfe...
                           69291,  # Ich bin...
                           69295,  # In dr FOSSGIS-Community bin ich aktiv ...
                           69293,  # Wo liegt dein Sourcecode?
                           73483,  # vollständige Adresse TB
                           ]:
                    continue
                # OSM-Samstag?
                elif itemID == 271553 and questions.get(71695, '') in \
                        ['',  # im Zweifel: nehmen wir an ja, Teilnehmer:in wird in Hamburg vor Ort sein
                         'Ich werde in Hamburg vor Ort sein.']:
                    badge.osm_samstag = True
                    if badge.ticket is None:
                        badge.ticket = itemName
                elif qid == 69219:  # Name Teilnehmerliste
                    badge.tl_name = qanswer
                elif qid == 100533:  # Ich mÃ¶chte meinen Namen und meine Email-Adresse in der Teilnehmer:innenliste verÃ¶ffentlichen.
                    badge.tl_veroeff = str(qanswer).lower() in ['true']
                elif qid == 69294:  # Name Englesystem
                    badge.engel = qanswer
                elif qid == 109418:  # Wie is dein Mappername?
                    badge.osm_name = qanswer
                elif qid == 109418:  # Wie is dein Nickname?
                    badge.nickname = qanswer
                else:
                    s = ""
                del qid, qname, qanswer

            ## Add other items
            if itemID == 416735:  # T-Shirt
                badge.tshirt = variationName
            elif itemID == 416736 :  # Helfende T-Shirt:
                badge.tshirt = variationName
            elif itemID == 416734:  # Ich möchte einen Tagungsband erhalten
                badge.tb = True
            elif itemID == 416734:  # Ihre vollstÃ¤ndige Versandadresse fÃ¼r gedruckten Tagungsband:
                badge.tb_adresse = ''
            elif itemID == 271558:  # Ich möchte eine Teilnehmer:innenliste erhalten
                badge.tl_erhalten = True
            elif itemID in [  # Mittagessen [268219, 274360, 274773, 281276, 275242]:
                268219,  # Mittagessen ( 3 x ) # x - fehlte, keine Bestellunge
                274360,  # Mittagessen für Helfer # x - fehlte
                416730,  # "Mittagessen (Mi, Do, Fr)"
                275242,  # Mittagessennachbuchung
                281276,  # Mittagessen für Helfende
            ]:

                badge.essen = variationName
            elif itemID == 451658:  # Ja, ich nehme an der Abendveranstaltung teil.
                badge.av = True
            elif itemID in EXKURSIONEN_IDs:
                badge.exkursionen.append(variationName)
            elif itemID in WORKSHOP_IDs:
                badge.workshops.append(variationName)
            elif itemID == 416739:  # OSM-Samstag
                badge.osm_samstag = True
            else:
                s = ""
            s = ""
    for k, badge in BADGES.items():
        if badge.company in [None, '']:
            if isinstance(badge.mail, str) and re.search(r'@(geo|student)?\.?hu-berlin\.de$', badge.mail):
                badge.company = 'Humboldt-Universität zu Berlin'

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
        header.append('needs_check')
        writer = csv.DictWriter(f, header, dialect=csvDialect)
        writer.writeheader()

        cnt = 0
        for person in badgeInfos:
            if CSV_LIMIT > 0 and cnt >= CSV_LIMIT:
                break
            data = {k: person.__dict__.get(k, None) for k in header}
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
                    if k == 'company':
                        v = replace_strings(v, REPLACE_IN_COMPANIES)
                    v = tex_escape(v)
                if k == 'name':
                    # Füge bei sehr langen Namen ein Leerzeichen ein
                    # damit auf dem Badge ein Zeilenumbruch entsteht
                    v = re.sub(r'(B\.?Sc|M\.?Sc|Dipl\.[- ]*(Geogr|Geol|Ing)\.?)[ ]+', '', v)
                    for rx in DELETE_FROM_NAMES:
                        v = rx.sub('', v)
                    v = re.sub(r'\(.+\)', '', v)
                    v = v.strip()
                    v = re.split(r'\|', v)[0]
                    if ',' in v:
                        print(f'Check "{v}"', file=sys.stderr)
                        data['needs_check'] = True
                    parts = re.split(r'[ ]+', v)
                    for i in range(len(parts)):
                        part = parts[i]
                        if len(part) > 15:
                            parts[i] = re.sub('-', '-""', part)
                    v = ' '.join(parts)
                data[k] = v
            writer.writerow(data)

            cnt += 1


if __name__ == '__main__':

    if PSEUDODATA:
        print('Create Badges with Pseudo-Data')
        badges = readPseudoBadgeInfos()
        PATH_BADGE_CSV = PATH_BADGE_CSV.parent / f'pseudodata.{PATH_BADGE_CSV.name}'
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

        if PATH_NREI.is_file():
            CompanyNames = readCompanyNames(PATH_NREI)
        else:
            CompanyNames = {}

        # 3. Lese Badge Data
        badges = readBadgeInfos(jsonData, companyNames=CompanyNames)

        if False:
            # füge Sondergäste hinzu
            from create_extra_badges import extra_badges

            for i, b in enumerate(extra_badges.values()):
                badges[f'guest_{i + 1}'] = b

            # Füge 10 leere Badges hinzu und
            emptyBadges = 10

            # Fülle A4 Blatt auf
            while (len(badges) + emptyBadges) % 4 != 0:
                emptyBadges += 1

            for i in range(emptyBadges):
                badges[f'empty_{i + 1}'] = BadgeInfo(name='')

            s = ""

    # 4. Schreibe badge CSV
    writeBadgeCsv(badges, PATH_BADGE_CSV)
    print("\nNumber of attendees: " + str(len(badges)))
