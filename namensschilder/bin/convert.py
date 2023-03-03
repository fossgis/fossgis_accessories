#!/usr/bin/python3
# -*- coding: utf-8 -*-
import codecs
import json, sys
import pathlib
import re
import csv
from collections import namedtuple
from typing import TypedDict

PATH_JSON = '2023_pretixdata.json'
PATH_CSV = 'pretix.csv'

PATH_JSON = pathlib.Path(PATH_JSON).resolve()
PATH_CSV = pathlib.Path(PATH_CSV).resolve()
PATH_ITEM = PATH_CSV.parent / re.sub(r'\.csv$', '_ITEM_IDs.csv', PATH_CSV.name)
s = ""

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
WORKSHOPS = {int(l[0]):','.join(l[1:]) for l in WORKSHOPS}
def normalize(name):
    name = name.replace(", BSc", "")
    if name.find(" (") > 0:
        name = name[:name.find(" (")]
    return name

def extractSurname(name):
    name = normalize(name)
    split = name.split(" ")
    return split[-1]

with open(PATH_JSON, 'r', encoding='utf-8') as f:
    #jsonString = f.read()
    #jsonString = codecs.decode(jsonString, 'unicode_escape')
    #data = json.loads(jsonString)
    data = json.load(f)

#print(json.dumps(data, indent=4))

items = {}
for item in data["event"]["items"]:
    items[item["id"]] = item["name"];
    for var in item["variations"]:
        items[var["id"]] = f'{item["name"]}::{var["name"]}'
    #print json.dumps(type, indent=4);

# print Items and write them into a CSV
print("Items:")
for key, value in items.items():
    print(f'{key}->{value}')

with open(PATH_ITEM, 'w', encoding='utf-8', newline='') as f:
    header = ['ItemID', 'Name']
    writer = csv.DictWriter(f, header)
    writer.writeheader()
    for key, value in items.items():
        writer.writerow(dict(ItemID=key, Name=value))
# IDs for FOSSGIS-Konferenzticket
#2023  
# ids = [268184,268185,268218,268218,268218,270039,272120,272122,272123]
# mit 271553 OSM Samstag
# ohne Onlineticket 274385,288025,288025,288025,288036

ids = [268184,268185,268218,268218,268218,270039,272120,272122,272123,271553]

persons = {}
for order in data["event"]["orders"]:
    #print("Next order:")
    names = []
    for pos in order["positions"]:
        if pos["item"] in ids and pos["attendee_name"]:
            names.append(pos["attendee_name"])
            persons[pos["attendee_name"]] = {0: pos["variation"]};

    print("Names: ")
    print(names)
    
    for pos in order["positions"]:
        #print(pos)
        if pos["attendee_name"]:
            name = pos["attendee_name"]
            if not name in persons:
                print(name + " has no ticket?!?")
                continue
            if pos["answers"]:
                persons[name][pos["item"]] = pos["answers"][0]["answer"]
            else:
                persons[name][pos["item"]] = 1                   
        else:
            for name in names:
                if not name in persons:
                    print(name + "has no ticket?!?")
                    continue
                if not pos["item"] in persons[name]:
                    if pos["answers"]:
                        persons[name][pos["item"]] = pos["answers"][0]["answer"]
                        break
                    else:
                        persons[name][pos["item"]] = 1


print("\nNumber of attendees: " + str(len(persons)))
#print(persons)

print("\nCSV:\n")


with open(PATH_CSV, 'w', encoding='utf-8', newline='') as f:
    header = ['Nachname', 'Vorname',
              'Ticket', 'TShirt', 'TBand', 'TListe',
              'AV', 'Mittag', 'WS', 'EX', 'OSM']

    writer = csv.DictWriter(f, header)
    writer.writeheader()

    for person, data in persons.items():
        # normalize name

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
        for it in items:
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
            'Nachname':nachname, 'Vorname':vorname,
            'Ticket':ticket, 'TShirt':tshirt, 'TBand':tband, 'TListe':tliste,
            'AV':av, 'Mittag':mittag,
            'WS': r'\\'.join(ws),
            'EX': r'\\'.join(ex),
            'OSM': osm,
        })


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
