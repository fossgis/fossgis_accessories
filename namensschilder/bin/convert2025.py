#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import csv
import datetime
import json
import locale
import random
import warnings
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple, Union
import os

from openpyxl import load_workbook, Workbook
from openpyxl.cell import Cell
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Alignment, Border, Font, Side

locale.setlocale(locale.LC_TIME, "de_DE.utf8")

# hier ggf. eine Liste mit order codes nutzen um selektiv badges zu erstellen
# https://pretix.eu/control/event/fossgis/2023/orders/<order code>/
#
ORDER_CODES = None
# ORDER_CODES = ['RK9LH']
# ORDER_CODES = ['BPJ3S']
# ORDER_CODES = ['XYMHH', 'BPJ3S']


# Hier die Fragecodes eintragen, deren Antworten in die CSV übernommen werden sollen
# siehe https://pretix.eu/control/event/fossgis/2025/questions/
# siehe data/questions.json
# {identifier : CSV Spaltenname}
CSV_QUESTIONS = {
    'YFHZVZCA': 'schild',
    'MBWBQDPJ': 'schild_firma',
    'NGMAWELJ': 'schild_nickname',
    'EA7G3AUG': 'name_engel1',
    'NAKTGXCW': 'name_engel2',
    'YNH7QNRG': 'name_osm',
    'QVL8CBHQ': 'tn_liste',
}

# Hier die Produkte (aka Items) eintragen, deren Antworten als Spalte in die CSV übernommen werden sollen
# siehe https://pretix.eu/control/event/fossgis/2025/items/
# siehe data/items.json
# {Produktname oder Product ID : CSV Spaltenname}
#
CSV_PRODUCTS = {
    'Konferenz-T-Shirt': 'tshirt',
    'Konferenz-T-Shirt Helfende': 'tshirt_helfer',
    'Ich nehme an der Abendveranstaltung teil.': 'av',
    'Ich möchte einen gedruckten Tagungsband erhalten.': 'tb',
}

# Hier die Produkt-ID (int) oder den Namen (str) der Exkursionen angeben
EXKURSIONEN = [
    'Geographischer Stadtrundgang',
    679198,
    675184,
]

# Hier können typos korrigiert, Firmennamen gekürzt und vereinheitlicht werden
DELETE_FROM_NAMES = [
    # re.compile(r'FD Vermesssung und Geodaten Stadt Hildesheim[ ]*'),
]
REPLACE_IN_COMPANIES = {
    # 'Bundesamt für Kartographie und Geodäsie': re.compile('(BKG|Bundesamt für Kartographie und Geodäsie)'),
}


# END SETTINGS


class BadgeInfo(object):
    """
    Alles Infos die in eine *.csv Zeile und mit einem Badge ausgedruckt werden sollen.
    """

    def __init__(self, order='', positionid=0):
        self.order: str = order
        self.posid: int = positionid
        self.vorname: str = ''
        self.name: str = ''
        self.firma: str = ''
        self.mail: str = ''
        self.ticket: str = ''
        self.exkursionen: List[str] = []
        self.workshops: List[str] = []
        self.status: str = ''

        # weitere zu erfassende Produkte / Fragen
        for q in list(CSV_QUESTIONS.values()) + list(CSV_PRODUCTS.values()):
            assert q not in self.__dict__.keys(), 'Duplicate key: ' + q
            self.__dict__[q] = None

    def __lt__(self, other):
        assert isinstance(other, BadgeInfo)
        if self.name != other.name:
            return self.name < other.name
        if self.vorname != other.vorname:
            return self.vorname < other.vorname
        return self.mail < other.mail

    def id(self) -> str:
        return f'{self.order}{self.posid}'

    def __str__(self):
        return f'Ticket:#{self.order},{self.name},{self.vorname}'


class csvDialect(csv.Dialect):
    """Describe the usual properties of Unix-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL


# escape LaTeX characters
# credits to https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
conv = {
    # '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    # '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\^{}',
    '\\': r'\textbackslash{}',
    '<': r'\textless{}',
    '>': r'\textgreater{}',
}
rx_tex_escape = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key=lambda item: - len(item))))


def tex_escape(text: Optional[str]) -> str:
    """
    :param text: a plain text message
    :return: the message escaped to appear correctly in LaTeX
    """
    if text is None:
        return ''
    return rx_tex_escape.sub(lambda match: conv[match.group()], text)


def replace_strings(text: str, replacements: dict):
    for newtext, oldtext in replacements.items():
        if isinstance(oldtext, str):
            text = text.replace(oldtext, newtext)
        if oldtext.search(text):
            return newtext
    return text


def itemName(item: dict) -> str:
    return item['name']['de']


def ticketItemIDs(products) -> List[int]:
    """
    Gibt alle jene item IDs zurück, die zu einem Ticket gehören für das
    ein Badge erstellt werden soll.
    :param products: list
    :param categories: list
    :return:
    """
    personalized = [item for item in products if item['personalized'] == True]
    on_site = [item for item in personalized if not re.search('online', itemName(item), re.IGNORECASE)]

    return [item['id'] for item in on_site]


def workshopItemIDs(products, categories) -> List[int]:
    cat_ids = [c['id'] for c in categories if re.search('^Workshop', itemName(c), re.IGNORECASE)]
    return [p['id'] for p in products if p['category'] in cat_ids]


def exkursionItemIDs(products, categories) -> List[int]:
    cat_ids = [c['id'] for c in categories if re.search('Exkursion', itemName(c), re.IGNORECASE)]
    return [p['id'] for p in products if p['category'] in cat_ids]


rx_online = re.compile('online', re.IGNORECASE)

LUT_Wochennamen = {
    'Montag': 'Mo',
    'Dienstag': 'Di',
    'Mittwoch': 'Mi',
    'Donnerstag': 'Do',
    'Freitag': 'Fr',
    'Samstag': 'Sa',
    'Sonntag': 'So',
}

# Pretix Order Status Names
# https://docs.pretix.eu/dev/api/resources/orders.html
ORDER_STATUS = {
    'e': 'expired',
    'c': 'canceled',
    'p': 'paid',
    'n': 'pending',
}


def readBadgeInfos(dir_json, order_status: List[str] = ['p', 'n', 'n', 'e']) -> List[BadgeInfo]:
    BADGES: Dict[str, BadgeInfo] = {}

    dir_json = Path(dir_json)
    assert dir_json.is_dir()

    PRODUCTS = readJson(dir_json / 'pretix_items.json')
    CATEGORIES = readJson(dir_json / 'pretix_categories.json')
    QUESTIONS = readJson(dir_json / 'pretix_questions.json')

    ORDERS = readJson(DIR_JSON / 'pretix_orders.json')
    if isinstance(ORDER_CODES, list):
        ORDERS = [o for o in ORDERS if o['code'] in ORDER_CODES]

    def itemIDs(pattern: str, is_category=False) -> List[int]:
        if is_category:
            cat_ids = [c['id'] for c in CATEGORIES if re.search(pattern, c['name']['de'])]
            return [p['id'] for p in PRODUCTS if p['category'] in cat_ids]
        else:
            return [c['id'] for c in PRODUCTS if re.search(pattern, c['name']['de'])]

    TicketIDs = ticketItemIDs(PRODUCTS)
    WorkshopIDs = workshopItemIDs(PRODUCTS, CATEGORIES)
    ExkursionIDs = exkursionItemIDs(PRODUCTS, CATEGORIES)

    PRODUCTS = {p['id']: p for p in PRODUCTS}
    CATEGORIES = {c['id']: c for c in CATEGORIES}

    TICKETS = {pid: p for pid, p in PRODUCTS.items() if pid in TicketIDs}
    WORKSHOPS = {pid: p for pid, p in PRODUCTS.items() if pid in WorkshopIDs}
    EXKURSIONEN = {pid: p for pid, p in PRODUCTS.items() if pid in ExkursionIDs}

    # Lese Bestellungen
    for order in ORDERS:
        ORDERCODE = order['code']
        if order['status'] not in order_status:
            print(f'Order {ORDER_STATUS[order['status']]}: {ORDERCODE}', file=sys.stderr)
            continue
        ORDER_BADGES = {}
        # Lese Positionen
        # eine Bestellung kann verschiedene Tickets beinhalten, denen wiederum andere positionen
        # zugeordnet sein können

        all_positions = {p['id']: p for p in order['positions']}
        unhandled_positions = {p['id']: p for p in order['positions']}

        # 1. Tickets lesen
        for (pid, pos) in [(pid, pos) for pid, pos in unhandled_positions.items() if pos['item'] in TicketIDs]:
            item_id = pos['item']
            badgeInfo = BadgeInfo(ORDERCODE, pos['positionid'])
            badgeInfo.status = ORDER_STATUS[order['status']]
            badgeInfo.mail = pos['attendee_email']

            name_parts = pos['attendee_name_parts']
            ticket = TICKETS[item_id]['name']['de']
            if '_scheme' not in name_parts:
                print(f'Überspringe Ticket ohne Namen: {ORDERCODE}: "{ticket}"', file=sys.stderr)
                unhandled_positions.pop(pid)
                continue
                s = ""
            if name_parts['_scheme'] == 'given_family':
                badgeInfo.name = name_parts['family_name']
                badgeInfo.vorname = name_parts['given_name']
            else:
                raise NotImplementedError(f"unknown name scheme {name_parts['_scheme']}")

            badgeInfo.ticket = ticket
            badgeInfo.firma = pos['company']

            for answer in pos['answers']:
                qid = answer['question_identifier']
                question = CSV_QUESTIONS.get(qid)
                if question:
                    setattr(badgeInfo, question, answer['answer'])

            ORDER_BADGES[pid] = badgeInfo
            unhandled_positions.pop(pid)

        # 2. Workshops lesen

        # 3. Verbleibenden Positionen den erstellten Badges zuordnen
        for (pid, pos) in [(pid, pos) for pid, pos in unhandled_positions.items()]:
            pos = unhandled_positions[pid]
            item_id = pos['item']
            product = PRODUCTS[item_id]
            product_name = itemName(product)
            product_id = product['id']

            addon_to = pos.get('addon_to')

            if addon_to:
                addon_base = all_positions[addon_to]
                addon_base_item = PRODUCTS[addon_base['item']]
                addon_base_name = itemName(addon_base_item)
            else:
                assert rx_online.search(product_name), f'Unbehandeltes Product: {product_name}'
                continue

            if addon_to not in ORDER_BADGES:
                assert rx_online.search(addon_base_name), \
                    f'Unbehandeltes Addon "{product_name}" für {addon_base_name}'
            else:
                badgeInfo: BadgeInfo = ORDER_BADGES[addon_to]

                variation_id = pos['variation']
                if variation_id:
                    value = [v['value']['de'] for v in product['variations'] if v['id'] == pos['variation']][0]
                else:
                    value = True

                if item_id in WorkshopIDs:
                    category = CATEGORIES[product['category']]
                    ws_time = category['name']['de']
                    ws_time = re.sub('Workshop|Uhr', '', ws_time).strip()
                    for kn, k2 in LUT_Wochennamen.items():
                        ws_time = re.sub(kn, k2, ws_time)
                    ws_time = ws_time.strip()
                    if ws_time == 'Do 9-10:30':
                        ws_time = 'Do 09:00-10:30'
                    badgeInfo.workshops.append(f'{ws_time}: {product_name}')
                elif item_id in ExkursionIDs:
                    badgeInfo.exkursionen.append(product_name)
                else:
                    if product_name in CSV_PRODUCTS:
                        setattr(badgeInfo, CSV_PRODUCTS[product_name], value)
                    elif product_id in CSV_PRODUCTS:
                        setattr(badgeInfo, CSV_PRODUCTS[product_id], value)

        for badge in ORDER_BADGES.values():
            assert badge.id() not in BADGES
            BADGES[badge.id()] = badge
    return list(BADGES.values())


def writeBadgeCsv(badgeInfos: List[BadgeInfo],
                  path_csv: Path,
                  fillA4: bool = False,
                  status: List[str] = ['paid']):
    path_csv = Path(path_csv)

    badgeInfos = [b for b in badgeInfos if b.status in status]

    n = len(badgeInfos)
    if n == 0:
        warnings.warn(Warning('empty list of badges'), stacklevel=2)
        return None

    def is_prio1(badge: BadgeInfo) -> bool:

        if badge.tb is True:
            return True
        if badge.tshirt:
            return True
        if badge.tshirt_helfer:
            return True
        return False

    # badges mit Tagungsband oder T-Shirt
    badges_prio1 = [p for p in badgeInfos if is_prio1(p)]
    prio1_persons = [(p.name, p.vorname, p.order) for p in badges_prio1]
    badges_prio2 = []
    for p in badgeInfos:
        if p not in badges_prio1:
            k = (p.name, p.vorname, p.order)

            # falls die Person bereits eine prio1 Person ist, füge auch andere Tickets ihr hinzu die
            # zu ihr in der gleichen Order bestellt wurden
            if k in prio1_persons:
                badges_prio1.append(p)
            else:
                badges_prio2.append(p)

    badges_prio1 = sorted([p for p in badges_prio1], key=lambda p: (p.name, p.vorname))
    badges_prio2 = sorted([p for p in badges_prio2], key=lambda p: (p.name, p.vorname))

    badgeInfos = badges_prio1 + badges_prio2

    if fillA4:
        while not len(badgeInfos) % 4 == 0:
            badgeInfos.append(BadgeInfo())

    print(f'Write {path_csv}')
    with open(path_csv, 'w', encoding='utf-8', newline='') as file:

        # schreibe alle Attribute als CSV Spalte
        p = badgeInfos[0]
        attributes = [k for k in p.__dict__.keys() if not k.startswith('_')]

        prio = ['order', 'posid', 'name', 'vorname', 'mail', 'ticket']
        header = [p for p in prio if p in attributes] + ['tütenprio']
        header += ['badge_type', 'badge_name', 'badge_zusatz']
        header += sorted([a for a in attributes if a not in header])
        header += ['needs_check']

        writer = csv.DictWriter(file, header, dialect=csvDialect)
        writer.writeheader()

        cnt = 0
        for i, person in enumerate(badgeInfos):
            data = {k: person.__dict__.get(k, None) for k in header}
            data.update(csv_badge_infos(person))
            data['tütenprio'] = 1 if person in badges_prio1 else 2
            csv_texify(data)
            writer.writerow(data)

            cnt += 1

    with open(path_csv, 'r') as file:
        assert len(file.readlines()) == cnt + 1


def csv_texify(data: Dict[str, Any]):
    """
    Wandelt enige CSV Einträge so um, dass sie gut in LaTeX
    ausgegeben werden können
    """
    for k in list(data.keys()):
        v = data[k]
        if isinstance(v, list):
            v = [line for line in v if isinstance(line, str) and len(line) > 0]
            latex = f'{len(v)}'
            if len(v) > 0:
                v = [tex_escape(line) for line in v]
                if True:
                    latex += r'\\ -- ' + r' \\ -- '.join(v)
                else:
                    # geht leider nicht, weil
                    latex += r' \begin{itemize} '
                    latex += r' \item ' + r' \item '.join(v)
                    latex += r' \end{itemize}\leavevmode '
            else:
                latex = '0'
            v = latex
        elif isinstance(v, str):
            # if k == 'company':
            #    v = replace_strings(v, REPLACE_IN_COMPANIES)
            v = tex_escape(v)
            pass

        if k in ['name', 'vorname']:
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
                    parts[i] = re.sub('-', '- ', part)
                    pass
            v = ' '.join(parts)
        data[k] = v


BADGE_TYPE = {
    '': 'CONF',  # Default ticket type = FOSSGIS Konferenz CONF
    'Konferenzticket': 'CONF',
    'Konferenzticket - reduzierter Preis': 'CONF',
    'Konferenzticket Beitragende': 'CONF',
    'Konferenzticket für Helfende': 'CONF',
    'Konferenzticket für Helfende (bezahlt)': 'CONF',
    'Konferenzticket Aussteller': 'CONF',
    'Konferenzticket - Community (OpenStreetMap und FOSSGIS)': 'CONF',
    'Hackathon #ifgiHACK25': 'HACK',
    'OpenStreetMap-Samstag': 'OSM',
    'Community Sprint': 'SPRINT',
}

BADGE_INFOS_OVERWRITES: Dict[str, Dict[str, str]] = {
    '<ORDERCODE>': {
        'badge_type': 'Veranstaltung: = CONF|OSM|HACK|SPRINT',
        'badge_name': 'Hauptname := Vorname Name|Firma|Nickname',
        'badge_zusatz': 'Namenszusatz := Firma|Nickname|foobar',
    }
}


def csv_badge_infos(badge: BadgeInfo) -> Dict[str, str]:
    d = dict()

    d['badge_type'] = BADGE_TYPE[badge.ticket]

    badge_name = f'{badge.vorname} {badge.name}'

    badge_zusatz = None
    if badge.schild == 'Name + Firma':
        badge_zusatz = badge.schild_firma
    elif badge.schild == 'Name + Nickname':
        badge_zusatz = badge.schild_nickname
    elif badge.schild == 'Nickname':
        badge_name = badge.schild_nickname

    d['badge_name'] = badge_name
    d['badge_zusatz'] = badge_zusatz

    if badge.order in BADGE_INFOS_OVERWRITES:
        d.update(BADGE_INFOS_OVERWRITES[badge.order])
    return d


def readPseudoBadgeInfos(dir_data: Union[str, Path]) -> List[BadgeInfo]:
    dir_data = Path(dir_data)
    assert dir_data.is_dir()
    # es werden verändert: Namen, Vornamen, emails, firmennamem
    # es wird genutzt: tatsächliche Bestelloptionen aus dem Pretix

    names = [('Max', 'Musterfamilie'),
             ('Maria', 'Musterfamilie'),
             ('Moritz', 'Musterfamilie'),
             ('Max', 'Power'),
             ('Langer-Doppelname', 'Ganz-Langer Familienname'),
             ('Isabel', 'Isernhagen'),
             ('Anna', 'Annaberg'),
             ('Charlotte', 'Charlottenburg'),
             ('David', 'Domaschke'),
             ('Karl-Gustav', 'Karlson vom Dach Familie'),
             ('Karl', 'Napf'),
             ('Rudi', 'Sorglos'),
             ('Dieter', 'Dosenkohl'),
             ('Vladimir', 'Vladimirowitsch'),
             ('Knecht', 'Ruprecht'),
             ('Tapferes', 'Schneiderlein'),
             ('Gestiefelter', 'Kater'),
             ('Prinzessin', 'Leia'),
             ('Lord Darth', 'Vader'),
             ('Jean-Luc', 'Piccard'),
             ]

    firmen = ['Firma mit sehr langem Namen',
              'Bundesamt für XY und Z',
              'Obelix Hinkelstein & Co GmbH',
              ]

    notes = [None,
             'weitere Anmerkungen, kurz gehalten',
             'so richtig viele weitere Anmerkungen und nochmal ganz andere Anmerkungen']

    real_badges = readBadgeInfos(dir_data)
    schild_optionen = list(set(b.schild for b in real_badges if b.schild))
    tshirs = list(set(b.tshirt for b in real_badges))
    tshirts_helfer = list(set(b.tshirt_helfer for b in real_badges))
    tickets = list(set(b.ticket for b in real_badges))
    exkursionen = set([])
    workshops = set([])
    for b in real_badges:
        for e in b.exkursionen:
            exkursionen.add(e)
        for w in b.workshops:
            workshops.add(w)
    exkursionen = list(exkursionen)
    workshops = list(workshops)
    BADGES = []

    def rnd(options: List, multiple: bool = False):
        if random.choice([True, False]):
            if multiple:
                return random.sample(options, random.choice(range(len(options))))
            else:
                return random.choice(options)

        else:
            if multiple:
                return []
            else:
                return None

    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for (vorname, name) in names:  # itertools.product(tickets, names) :
        badge = BadgeInfo()
        badge.name = name
        badge.vorname = vorname
        badge.order = ''.join(random.sample(letters, 5))
        badge.ticket = random.choice(tickets)
        badge.av = random.choice([True, False])
        badge.tb = random.choice([True, False])
        badge.mail = f'{badge.vorname}.{badge.name}@nomail.xyz'.lower()
        badge.tshirt = rnd(tshirs)
        badge.tshirt_helfer = rnd(tshirts_helfer)
        badge.workshops = rnd(workshops, multiple=True)
        badge.exkursionen = rnd(exkursionen, multiple=True)
        schild = random.choice(schild_optionen)
        badge.schild = schild
        if 'Firma' in schild:
            badge.schild_firma = random.choice(firmen)
        if 'Nickname' in schild:
            badge.schild_nickname = 'nick_' + vorname.lower()
        badge.notes = rnd(notes)
        badge.firma = random.choice(firmen)

        if (badge.vorname, badge.name) == ('Moritz', 'Musterfamilie'):
            badge.av = True
            badge.ticket = 'Konferenzticket für Helfende (bezahlt)'

        BADGES.append(badge)
    return BADGES


def readJson(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def remove_ws(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def get_sheet(name: str, book: Workbook) -> Worksheet:
    if name in book.sheetnames:
        sheet = book[name]
        sheet.delete_cols(1, sheet.max_column)
    else:
        sheet = book.create_sheet(name)
    return sheet


def get_workbook(path_xlsx: Union[str, Path]) -> Workbook:
    path_xlsx = Path(path_xlsx)
    if path_xlsx.is_file():
        book = load_workbook(filename=path_xlsx.as_posix())
    else:
        book = Workbook()
    for s in book.sheetnames[:]:
        del book[s]
    return book


thin_bottom_border = Border(bottom=Side(style='thin'))
bold_font = Font(bold=True)
top_alignment = Alignment(vertical="top")


def writeTeilnehmerliste(badges: List[BadgeInfo],
                         path_xlsx: Union[str, Path],
                         status: List[str] = ['paid']):
    path_xlsx = Path(path_xlsx)

    badges = sorted([b for b in badges if b.tn_liste and b.status in status])

    book = get_workbook(path_xlsx)
    sheet = get_sheet('Teilnehmer', book)

    sheet.cell(1, 1, 'Teilnehmerliste FOSSGIS 2025')
    sheet.merge_cells('A1:D1')
    row = 3
    for c, n in enumerate(['Name', 'Vorname', 'Email', 'Firma/Organisation']):
        sheet.cell(row, c + 1, n)
        sheet.cell(row, c + 1).border = thin_bottom_border
        sheet.cell(row, c + 1).font = bold_font

    for b in badges:
        row += 1
        infos = [b.name, b.vorname, b.mail, b.firma]

        for c, info in enumerate(infos):
            sheet.cell(row, c + 1, info)
    enlarge_columns(sheet)
    book.save(path_xlsx)


def writeAllOrders(badges: List[BadgeInfo], path_xlsx: Union[str, Path]):
    path_xlsx = Path(path_xlsx)
    book = get_workbook(path_xlsx)
    badges = sorted(badges)
    sheet = get_sheet('Alle Tickets', book)
    sheet.cell(1, 1, 'FOSSGIS 2025 - Alle Bestellungen')
    sheet.merge_cells('A1:D1')
    row = 3
    for c, n in enumerate(
            ['Name', 'Vorname', 'Order', 'Email', 'Status', 'Ticket',
             'AV', 'TB', 'T-Shirt', 'T-Shirt-Helfer',
             'Workshops']):
        sheet.cell(row, c + 1, n)
        sheet.cell(row, c + 1).border = thin_bottom_border
        sheet.cell(row, c + 1).font = bold_font

    row_start = row
    for b in badges:
        row += 1
        infos = [b.name, b.vorname, b.order, b.mail, b.status, b.ticket,
                 b.av, b.tb, b.tshirt, b.tshirt_helfer, '\n'.join(b.workshops)]

        for c, info in enumerate(infos):
            sheet.cell(row, c + 1, info)

    table = Table(displayName="TabelleBestellungen", ref=f'A{row_start}:K{row}')
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium9",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,  # Alternierende Zeilenfarben
        showColumnStripes=False
    )
    sheet.add_table(table)
    enlarge_columns(sheet)
    book.save(path_xlsx)


def writeCancelations(badges: List[BadgeInfo], path_xlsx: Union[str, Path]):
    path_xlsx = Path(path_xlsx)
    badges = sorted([b for b in badges if b.status == 'canceled'])
    book = get_workbook(path_xlsx)
    sheet = get_sheet('Stornierungen', book)
    sheet.cell(1, 1, 'Stornierung FOSSGIS 2025')
    sheet.merge_cells('A1:D1')
    row = 3
    for c, n in enumerate(['Name', 'Vorname', 'Order', 'Email', 'status']):
        sheet.cell(row, c + 1, n)
        sheet.cell(row, c + 1).border = thin_bottom_border
        sheet.cell(row, c + 1).font = bold_font

    for b in badges:
        row += 1
        infos = [b.name, b.vorname, b.order, b.mail, b.status]

        for c, info in enumerate(infos):
            sheet.cell(row, c + 1, info)
    enlarge_columns(sheet)
    book.save(path_xlsx)


def writeHelferTShirtList(badges: List[BadgeInfo], path_xlsx: Union[str, Path]):
    path_xlsx = Path(path_xlsx)

    badges = sorted([b for b in badges if b.tshirt_helfer])

    book = get_workbook(path_xlsx)
    sheet = get_sheet('Teilnehmer', book)

    sheet.cell(1, 1, 'Helfer-T-Shirts FOSSGIS 2025')
    sheet.merge_cells('A1:D1')
    row = 3
    for c, n in enumerate(['Name', 'Vorname', 'Order', 'Email', 'Helfer T-Shirt']):
        sheet.cell(row, c + 1, n)
        sheet.cell(row, c + 1).border = thin_bottom_border
        sheet.cell(row, c + 1).font = bold_font

    for b in badges:
        row += 1
        infos = [b.name, b.vorname, b.order, b.mail, b.tshirt_helfer]

        for c, info in enumerate(infos):
            sheet.cell(row, c + 1, info)
    enlarge_columns(sheet)
    book.save(path_xlsx)


def enlarge_columns(sheet: Worksheet):
    """
    Vergrößert die Spaltenbreiten
    """
    # Automatische Spaltenbreiten berechnen
    for col in sheet.columns:
        max_length = 0
        for c in col:
            if isinstance(c, Cell):
                col_letter = c.column_letter  # Holt den Buchstaben der Spalte
                break
        for cell in col:
            try:
                if cell.value == 'Unterschrift':
                    max_length = 40
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass

        sheet.column_dimensions[col_letter].width = max_length + 2  # Puffer hinzufügen


def writeWorkshopLists(badges: List[BadgeInfo], talks: list[Dict], path_xlsx: Union[str, Path]):
    path_xlsx = Path(path_xlsx)
    badges = [b for b in badges if len(b.workshops) > 0 and b.status in ['paid']]

    workshops = [t for t in talks if t['submission_type']['de-formal'].startswith('Workshop')]
    not_confirmes = [t for t in workshops if t['state'] != 'confirmed']
    workshops = sorted(workshops, key=lambda t: (t['slot']['start'], t['slot']['room']['de-formal']))
    for i in range(len(workshops)):
        talk = workshops[i]
        talk['title'] = remove_ws(talk['title'])

        if 'room' not in talk['slot']:
            s = ""

    workshops = {t['title']: t for t in workshops}

    if len(badges) == 0:
        print('Keine Workshops gefunden', file=sys.stderr)
        return

    # sortiere nach Workshop
    workshops_participants: Dict[Tuple, List[BadgeInfo]] = dict()

    rx_ws_name = re.compile(r'(?P<day>[^ ]+) (?P<time>[^ ]+): (?P<name>.+)$')

    # Apply top alignment to cell A1
    for b in badges:
        for w in b.workshops:
            match = rx_ws_name.match(w)
            ws_day = match.group('day')
            ws_time = match.group('time')
            ws_name = match.group('name')

            # k = (ws_day, ws_time, ws_name)
            workshops_participants[ws_name] = workshops_participants.get(ws_name, []) + [b]

    book = get_workbook(path_xlsx)

    # 1. Übersicht der Workshops + Raum + Zeit
    sheet = get_sheet('Workshops', book)
    row = 1
    for c, n in enumerate(['Tag', 'Zeit', 'Raum', 'Workshop']):
        sheet.cell(row, 1 + c, n)
        sheet.cell(row, 1 + c).border = thin_bottom_border
        sheet.cell(row, 1 + c).font = bold_font

    for ws in sorted(workshops.values(), key=lambda t: (t['slot']['start'], t['slot']['room']['de-formal'])):
        row += 1
        dtg = datetime.datetime.fromisoformat(ws['slot']['start'])

        room = ws['slot']['room']['de-formal']
        for c, value in enumerate([dtg.strftime('%a %d.%m.'),
                                   dtg.strftime('%H:%M'),
                                   room,
                                   ws['title']]):
            sheet.cell(row, 1 + c, value)

    # 2. Überischt über alle Teilnehmenden
    sheetAll = get_sheet('All', book)

    row = 1
    for c, n in enumerate(['Tag', 'Zeit', 'Dauer', 'Raum', 'Workshop', 'Name', 'Vorname', 'Mail', 'Order']):
        sheetAll.cell(row, 1 + c, n)
        sheetAll.cell(row, 1 + c).border = thin_bottom_border
        sheetAll.cell(row, 1 + c).font = bold_font

    for ws in workshops.values():
        ws_name = ws['title']
        for badge in sorted(workshops_participants.get(ws_name, []), key=lambda b: (b.name, b.vorname)):
            row += 1
            talk: dict = workshops[ws_name]
            dtg = datetime.datetime.fromisoformat(talk['slot']['start'])
            duration = talk['duration']
            room = talk['slot']['room']['de-formal']

            for c, value in enumerate([dtg.strftime('%a %d.%m.'),
                                       dtg.strftime('%H:%M'),
                                       duration,
                                       room, ws_name, badge.name, badge.vorname, badge.mail, badge.order]):
                sheetAll.cell(row, 1 + c, value)

    table_range = f"A1:G{row}"
    table = Table(displayName=sheetAll.title, ref=table_range)
    style = TableStyleInfo(
        name="TableStyleMedium9",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,  # Alternierende Zeilenfarben
        showColumnStripes=False
    )
    sheetAll.add_table(table)

    # write table for each workshop
    if True:
        for ws in sorted(workshops.values(), key=lambda t: (t['slot']['start'], t['slot']['room']['de-formal'])):
            ws_name = ws['title']
            if ws['state'] != 'confirmed':
                s = ""
                continue
            if ws_name not in workshops_participants:
                print(f'Keine Teilnehmenden für {ws_name} gefunden', file=sys.stderr)

            participants = sorted(workshops_participants.get(ws_name, []), key=lambda b: (b.vorname, b.name))
            dtg = datetime.datetime.fromisoformat(ws['slot']['start'])
            dtg2 = datetime.datetime.fromisoformat(ws['slot']['end'])
            speakers = [s['name'] for s in ws['speakers']]
            room = ws['slot']['room']['de-formal']
            sheet_name = f"{dtg.strftime('%a%H%M')}_{room.split(' ')[0]}"
            sheet = get_sheet(sheet_name, book)

            row = 1
            lines = [['Workshop', ws_name],
                     ['Tag', dtg.strftime('%a %d.%m.')],
                     ['Zeit', dtg.strftime('%H:%M')],
                     ['Ende', dtg2.strftime('%H:%M')],
                     ['Raum', room],
                     ['Leitung', ', '.join(speakers)],
                     [],
                     ['Name', 'Vorname', 'Mail', 'Order', 'Unterschrift'],
                     ]
            for p in participants:
                lines.append([p.name, p.vorname, p.mail, p.order, ''])

            for line in lines:
                for c, n in enumerate(line):
                    sheet.cell(row, 1 + c, n)
                row += 1

            r_headline = row - len(participants) - 1
            for c in range(1, 6):
                sheet.cell(r_headline, c).border = thin_bottom_border
                sheet.cell(r_headline, c).font = bold_font

            for r in range(r_headline + 1, row):
                sheet.row_dimensions[r].height = 30
                for c in range(1, 6):
                    sheet.cell(r, c).border = thin_bottom_border
                    sheet.cell(r, c).alignment = top_alignment

            sheet.merge_cells('B1:D1')
            sheet.merge_cells('B6:D6')

    for s in book.sheetnames:
        sheet = book[s]
        enlarge_columns(sheet)

    path_xlsx = Path(path_xlsx)
    book.save(path_xlsx.as_posix())


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Erstelle Badges & Workshoplisten')
    parser.add_argument('-p', '--pseudodata',
                        required=False,
                        default=False,
                        help='Verwende pseudonomisierte daten, etwa für eine Vorschau',
                        action='store_true')
    parser.add_argument('-w', '--workshoplisten',
                        required=False,
                        default=True,
                        help='Schreibe workshoplisten',
                        action='store_true')

    parser.add_argument('--csv_limit',
                        required=False,
                        default=None,
                        help='Limitiere CSV outputs auf n zeilen',
                        )
    parser.add_argument('-y', '--year',
                        type=int,
                        default=datetime.date.today().year,
                        help='Jahr der FOSSGIS')

    # CSV_LIMIT
    # beschränkt das aus der json generierte CSV auf CSV_LIMIT Zeilen.
    # Gut um schnell zu testen ob das PDF sinnvoll aussieht

    args = parser.parse_args()

    EVENT_ID = f'{args.year}'
    ROOT = Path(__file__).parents[1]
    DIR_JSON = ROOT / 'json'
    DIR_CSV = ROOT / 'csv'
    os.makedirs(DIR_CSV, exist_ok=True)

    # 1. read badges
    if False or args.pseudodata:
        #  pseudonymisierte Beispieldaten
        print('Create pseudo tickets')
        badges = readPseudoBadgeInfos(DIR_JSON)
        path_csv = DIR_CSV / f'badges{EVENT_ID}_pseudo.csv'
        writeBadgeCsv(badges, path_csv)
        exit(0)

    badges = readBadgeInfos(DIR_JSON)
    talks = readJson(DIR_JSON / 'pretalx_talks.json')

    if True:
        # schreibe Workshop liste
        path_xlsx = DIR_CSV / f'{EVENT_ID}_workshops.xlsx'
        writeWorkshopLists(badges, talks, path_xlsx)

    if True:
        path_xlsx = DIR_CSV / f'{EVENT_ID}_teilnehmerliste.xlsx'
        writeTeilnehmerliste(badges, path_xlsx, status=['paid'])

        path_xlsx = DIR_CSV / f'{EVENT_ID}_helfertshirts.xlsx'
        writeHelferTShirtList(badges, path_xlsx)

        path_xls = DIR_CSV / f'{EVENT_ID}_cancelations.xlsx'
        writeCancelations(badges, path_xls)

        path_xlsx = DIR_CSV / f'{EVENT_ID}_AlleBestellungen.xlsx'
        writeAllOrders(badges, path_xlsx)

    if True:
        # Schreibe CSV dateien
        if False:
            # Schreibe ein großes CSV
            path_csv = DIR_CSV / f'badges{EVENT_ID}_tickets.csv'
            writeBadgeCsv(badges, path_csv, status=['paid'])

        else:
            # Separiere badges nach Ticket-Typ
            tickets = set([b.ticket for b in badges])

            ticket_types = {
                # file suffix: ticket name prefix
                'confosm': re.compile(r'^(Konferenz|OpenStreetMap)'),
                'hackathon': re.compile(r'^Hackathon'),
                'sprint': re.compile(r'^Community Sprint'),
            }
            for suffix, rx_prefix in ticket_types.items():

                ticket_badges = [v for v in badges if rx_prefix.search(v.ticket)]
                path_csv = DIR_CSV / f'badges{EVENT_ID}_{suffix}.csv'

                if args.csv_limit:
                    ticket_badges = ticket_badges[:min(len(ticket_badges), args.csv_limit)]

                if len(ticket_badges) > 0:
                    writeBadgeCsv(ticket_badges, path_csv, status=['paid'])
                    print(f'{path_csv} : {len(ticket_badges)} tickets')
                else:
                    warnings.warn(f'No "{suffix}={rx_prefix}" tickets found')
    if False:
        # Füge leere Badges hinzu und
        emptyBadges = 30
        # Fülle auf A4 Blatt auf (4 Badges pro Blatt)
        while emptyBadges % 4 != 0:
            emptyBadges += 1

        badges = [BadgeInfo() for i in range(emptyBadges)]
        path_csv = DIR_CSV / f'badges{EVENT_ID}_leer.csv'
        writeBadgeCsv(badges, path_csv)
        print(f'{path_csv} : {len(badges)} tickets')

    print('Done')
