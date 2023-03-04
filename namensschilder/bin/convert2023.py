#!/usr/bin/python3
# -*- coding: utf-8 -*-
import codecs
import collections
import json, sys
import pathlib
import re
import csv
from collections import namedtuple
from typing import TypedDict

PATH_JSON = '2023_pretixdata.json'
PATH_PERSONEN_CSV = 'pretix.csv'

PATH_JSON = pathlib.Path(PATH_JSON).resolve()
PATH_PERSONEN_CSV = pathlib.Path(PATH_PERSONEN_CSV).resolve()
PATH_ITEM_CSV = PATH_PERSONEN_CSV.parent / re.sub(r'\.csv$', '_ITEM_IDs.csv', PATH_PERSONEN_CSV.name)
s = ""
CSV_LIMIT = 25

# Auflistung der Workshops

WORKSHOPS = '''
270040,Punktwolkeverarbeitung und Analyse mit PDAL
270041,QGIS 3 Workshop
270042,MapProxy im Praxiseinsatz
270043,QGIS-Pluginentwicklung mit Python
270044,Hands on basemap.de
270045,Die Open Database License (ODbL) der OpenStreetMap-Daten
270046,PostgreSQL / PostGIS Workshop für Einsteiger
270047,Orchestrierung einer GDI über Docker
270048,Webmapping in nur 90 Minuten mit Leaflet
270049,Masterportal in der Praxis
270051,Geodateninfrastruktur mit Docker
271545,"QGIS 3D, LiDAR Punktwolken und Profilwerkzeug"
271541,Mobiles QGIS mit merginmaps
271542,Einführung GeoServer
271543,Mapbender - Einstieg in den Aufbau von WebGIS-Anwendungen
270050,Oberflächenklassifikation aus Luft- und Satellitenbildern mit Hilfe von actinia
271544,Openstreetmap-Daten mit ogr2ogr und SQL für QGIS aufbereiten
271546,Datenschutz und geographische Informationen
271547,React basierte WebGIS Clients mit MapComponents & MapLibre-gl
282424,Nahtlose Feldarbeit dank QField und QFieldCloud
271548,Formulare gestalten in QGIS
271550,"GDI ""instant"""
271551,Update your MapServer from 7 to 8
272135,Workshopnachbuchung
'''

WORKSHOPS = [l for l in WORKSHOPS.split('\n') if len(l) > 0]
WORKSHOPS = [l.split(',') for l in WORKSHOPS]
WORKSHOPS = {int(l[0]): ','.join(l[1:]) for l in WORKSHOPS}


class csvDialect(csv.Dialect):
    """Describe the usual properties of Unix-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL


def normalize(name):
    name = name.replace(", BSc", "")
    if name.find(" (") > 0:
        name = name[:name.find(" (")]
    return name


def extractSurname(name):
    name = normalize(name)
    split = name.split(" ")
    return split[-1]


# print(json.dumps(data, indent=4))

def read_event_items(data: dict) -> dict:
    """
    Liest alles Event Items ein
    :param data:
    :return: dict
    """
    items = {}
    for item in data["event"]["items"]:
        iid = item['id']
        iname = item['name']
        items[iid] = iname
        for var in item["variations"]:
            vid = var["id"]
            assert vid not in items
            items[vid] = f'{iname}::{var["name"]}'
        # print json.dumps(type, indent=4);
    items = collections.OrderedDict(sorted(items.items()))
    return items


def read_event_questions(data: dict) -> dict:
    questions = {}
    for question in data['event']['questions']:
        qid = question['id']
        assert qid not in questions
        questions[qid] = question['question']

    return questions


def write_event_items(items: dict, path_csv: pathlib.Path):
    path_csv = pathlib.Path(path_csv)
    # print Items and write them into a CSV
    with open(path_csv, 'w', encoding='utf-8', newline='') as f:
        header = ['ItemID', 'Name']
        writer = csv.DictWriter(f, header)
        writer.writeheader()
        for key, value in items.items():
            writer.writerow(dict(ItemID=key, Name=value))


class Person(object):

    def __init__(self):
        self.name: str = None
        self.mail: str = None
        self.ticket: str = None
        self.name_teilnehmer_liste: str = None
        self.name_veroeffentlichen: bool = False
        self.essen: str = None
        self.tshirt: str = None
        self.tagungsband: str = None
        self.anwers: dict = {}


def read_person_data(data: dict,
        ticket_items = [],
        workshop_items = [],
        tshirt_items = [],
                     ) -> dict:
    PERSONS = {}

    items = read_event_items(data)
    questions = read_event_questions(data)

    for cntOrder, order in enumerate(data["event"]["orders"]):
        # !eine Order kann mehrere Tickets enthalten!
        # ?eine Order kann mehrere T-Shirts enthalten?
        orderCode = order['code']
        personsInOrder = {}
        if False and orderCode not in [#'RS3XX',
                                 #'RKYE7',
                                 '3GQTR']:
            continue
        person: Person = None
        for cntPos, pos in enumerate(order["positions"]):
            pos: dict

            iid = pos['item']
            vid = pos['variation']
            iname = items[iid]
            vname = items[vid] if vid else iname
            answers = pos['answers']
            name = pos['attendee_name']
            if iid in [272120, # Konferenzticket Beitragende
                       268184, # Konferenzticket
                       268185, #->Konferenzticket Community
                       268218, #->Konferenzticket - reduzierter Preis
                       270039, #->Konferenzticket fÃ¼r Helfende
                       ]:
                person = Person()
                person.name == name
                assert name not in personsInOrder
                assert name not in PERSONS
                PERSONS[name] = person
                # Ticket typ?
                person.ticket = vname
                s = ""
            else:
                s = ""
            for answer in answers:
                qid = answer['question']
                qname = questions[qid]
                qanswer = answer['answer']
                if qid is None:
                    s = ""
                if qid in person.anwers:
                    continue
                assert qid not in person.anwers

                person.anwers[qid] = qanswer
                if qid == 69219:
                    person.name_teilnehmer_liste = qanswer
                elif qid == 69290:
                    person.name_veroeffentlichen = qanswer
                elif qid == 73483: # Adresse Tagungsband
                    person.tagungsband = qanswer
                else:
                    s = ""

    return PERSONS


# print(persons)


def write_person_data(persons: dict, path_csv: pathlib.Path):
    path_csv = pathlib.Path(path_csv)
    print("\nCSV:\n")
    with open(path_csv, 'w', encoding='utf-8', newline='') as f:
        header = ['Nachname', 'Vorname',
                  'Ticket', 'TShirt', 'TBand', 'TListe',
                  'AV', 'Mittag', 'WS', 'EX', 'OSM']

        writer = csv.DictWriter(f, header, dialect=csvDialect)
        writer.writeheader()

        cnt = 0
        for person, data in persons.items():
            if CSV_LIMIT > 0 and cnt >= CSV_LIMIT:
                break
            name = normalize(person)
            nachname = extractSurname(name)
            vorname = name[0:-len(nachname)].strip()
            ticket = None
            tshirt = None
            tband = False
            tliste = False
            av = False
            mittag = None
            ws = []
            ex = []
            osm = False
            others = []
            for it, itemValue in data.items():
                if it not in items.keys():
                    continue
                itemName = items[it]

                if it in WORKSHOPS.keys():
                    ws.append(WORKSHOPS[it])
                elif re.search(r'ticket', itemName, re.I):
                    ticket = itemName
                elif re.search(r'^Exkursion', itemName, re.I):
                    ex.append(itemName)
                elif re.search(r'^Mittagessen', itemName, re.I):
                    mittag = itemName
                elif re.search(r'Tagungsband', itemName, re.I):
                    tband = True
                elif re.search(r'^T-Shirt( Helfende)?::', itemName, re.I):
                    tshirt = itemName.split('::')[1]
                elif re.search(r'Abendveranstaltung', itemName, re.I):
                    av = True
                elif re.search(r'Teilnehmer:innenliste', itemName, re.I):
                    tliste = True
                elif re.search(r'OSM-Samstag', itemName, re.I):
                    osm = True
                else:
                    if itemName in ['T-Shirt', 'T-Shirt Helfende']:
                        continue
                    others.append(itemName)
                    header = ['Nachname', 'Vorname',
                              'Ticket', 'TShirt', 'TBand', 'TListe',
                              'AV', 'Mittag', 'WS', 'EX', 'OSM']

            writer.writerow({
                'Nachname': nachname,
                'Vorname': vorname,
                'Ticket': ticket,
                'TShirt': tshirt,
                'TBand': tband,
                'TListe': tliste,
                'AV': av,
                'Mittag': mittag,
                'WS': r'\\'.join(ws),
                'EX': r'\\'.join(ex),
                'OSM': osm,
            })

            cnt += 1


if False:
    # print header:
    f.write("Name;Nachname;Variant;WSCount")
    for it in items:
        f.write(";" + str(it))
    f.write("\n")

    for person in persons:
        f.write(normalize(person) + ";")
        f.write(extractSurname(person) + ";")
        dict = persons[person]
        f.write(str(dict[0]))

        count = 0
        for it in items:
            if it in dict and "Workshop" in items[it]:
                count += 1

        f.write(";" + str(count))

        for it in items:
            if it in dict:
                out = str(dict[it]).replace("\r", "").replace("\n", "\\n").replace(";", "").replace("_", "\\_")
                f.write(";" + out)
            else:
                f.write(";")
        f.write("\n")

    f.flush()

if __name__ == '__main__':
    # 1. lese JSON
    with open(PATH_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. lese &  schreibe items + variations aka Dinge die gebucht werden können
    items = read_event_items(data)
    questions = read_event_questions(data)
    print("Items:")
    for key, value in items.items():
        print(f'{key}->{value}')
    write_event_items(items, PATH_ITEM_CSV)

    print('Questions:')
    for key, value in questions.items():
        print(f'{key}->{value}')

    # 3. schreibe personen daten
    persons = read_person_data(data)
    ANSWERS = {
        69219: 'TL_Name'
    }
    write_person_data(persons, ANSWERS, PATH_PERSONEN_CSV)
    print("\nNumber of attendees: " + str(len(persons)))
