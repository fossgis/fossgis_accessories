#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json, sys


def normalize(name):
    name = name.replace(", BSc", "")
    if name.find(" (") > 0:
        name = name[:name.find(" (")]
    return name

def extractSurname(name):
    name = normalize(name)
    split = name.split(" ")
    return split[-1]


f = open('pretixdata.json', 'r');
data = json.load(f);

#print(json.dumps(data, indent=4))

items = {}
for type in data["event"]["items"]:
    items[type["id"]] = type["name"];
    for var in type["variations"]:
        items[var["id"]] = var["name"]
    #print json.dumps(type, indent=4);

print("Items:")
for it in items:
    print(str(it) + " -> " + items[it])

# IDs for FOSSGIS-Konferenzticket
ids = [8821, 8822, 8826, 8827, 8830, 8835]

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
f = open('pretix.csv', 'w');

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
            out = str(dict[it]).replace("\r", "").replace("\n", "\\n").replace(";", "")
            f.write(";" + out)
        else:
            f.write(";")
    f.write("\n")
            
f.flush()
