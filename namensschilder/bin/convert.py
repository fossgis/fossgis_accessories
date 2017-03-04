#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json, sys

f = open('pretixdata.json', 'r');
data = json.load(f);

print(json.dumps(data, indent=4))

items = {}
for type in data["event"]["items"]:
    items[type["id"]] = type["name"];
    for var in type["variations"]:
        items[var["id"]] = var["name"]
    #print json.dumps(type, indent=4);

print("Items:")
for it in items:
    print(str(it) + " -> " + items[it])
# 242 is FOSSGIS-Konferenzticket

persons = {}
for order in data["event"]["orders"]:
    #print("Next order:")
    names = []
    for pos in order["positions"]:
        if pos["item"] == 242 and pos["attendee_name"]:
            names.append(pos["attendee_name"])
            persons[pos["attendee_name"]] = {0: pos["variation"]};

    #print("Names: ")
    #print(names)
    
    for pos in order["positions"]:
        #print(pos)
        if pos["attendee_name"]:
            name = pos["attendee_name"]
            if not name in persons:
                print(name + "has no ticket?!?")
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

# print header:
sys.stdout.write("Name;Variant")
for it in items:
    sys.stdout.write(";" + str(it))
sys.stdout.write("\n")

for person in persons:
    sys.stdout.write(person + ";")
    dict = persons[person]
    sys.stdout.write(str(dict[0]))
    
    for it in items:
        if it in dict:
            out = str(dict[it]).replace("\r", "").replace("\n", "\\n").replace(";", "")
            sys.stdout.write(";" + out)
        else:
            sys.stdout.write(";")
    sys.stdout.write("\n")
            
sys.stdout.flush()
