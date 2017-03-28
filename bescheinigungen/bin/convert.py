#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json, sys, operator

def normalize_ws(ws):
    return ws.replace("/","")

def normalize(name):
    name = name.replace(", BSc", "")
    if name.find(" (") > 0:
        name = name[:name.find(" (")]
    return name

def extractSurname(name):
    name = normalize(name)
    split = name.split(" ")
    return split[-1]

def extractPrename(name):
    name = normalize(name)
    return name.replace(extractSurname(name), "")

def extractShortTicketName(ticket):
    split = ticket.split(" - ")
    return split[0]

f = open('pretixdata.json', 'r');
data = json.load(f);

print(json.dumps(data, indent=4))

items = {}
for type in data["event"]["items"]:
    if type["active"]:
       items[type["id"]] = type["name"];
       for var in type["variations"]:
           items[var["id"]] = var["name"]
#    print(json.dumps(type, indent=4))

print("\nItems:")
for it in items:
    print(str(it) + " -> " + items[it])
# 242 is FOSSGIS-Konferenzticket

workshops = {}
for it in items:
    if "Workshop -" in items[it]:
       workshops[it] = items[it];
       
workshops_sorted = sorted(workshops, key=workshops.get)

print("\nWorkshops:")
for ws in workshops_sorted:
    print(str(ws) + " -> " + workshops[ws])

persons = {}
for order in data["event"]["orders"]:
    #print("Next order:")
    names = []
    for pos in order["positions"]:
        if pos["item"] == 242 and pos["attendee_name"]:
            names.append(pos["attendee_name"])
            if pos["attendee_name"] in persons:
                print("WARNING: attandee has two tickets: "+pos["attendee_name"]+"!!!")
            persons[pos["attendee_name"]] = {0: pos["variation"]};

    #print("Names: ")
    #print(names)
    
    for pos in order["positions"]:
        #print(pos)
        if pos["attendee_name"]:
            name = pos["attendee_name"]
            if not name in persons:
                print(name + " has no ticket?!? - Item: " + items[pos["item"]])
                continue
            if pos["answers"]:
                persons[name][pos["item"]] = pos["answers"][0]["answer"]
            else:
                persons[name][pos["item"]] = 'x'                   
        else:
            for name in names:
                if not name in persons:
                    print(name + " has no ticket?!? - Item: " + items[pos["item"]])
                    continue
                if not pos["item"] in persons[name]:
                    if pos["answers"]:
                        persons[name][pos["item"]] = pos["answers"][0]["answer"]
                        break
                    else:
                        persons[name][pos["item"]] = 'x'


print("\nNumber of attendees: " + str(len(persons)))
#print(persons)

print("\nCSV:\n")
f = open('pretixdata.csv', 'w');

# print header:
f.write("Name;Nachname;Variant;WSCount")
for it in items:
    f.write(";\"" + str(items[it]) + "\"")
f.write("\n")

for person in persons:
    f.write(normalize(person) + ";")
    f.write(extractSurname(person) + ";")
    dict = persons[person]
    f.write(extractShortTicketName(items[dict[0]]))

    count = 0
    for it in items:
        if it in dict and "Workshop" in items[it]:
            count += 1

    f.write(";" + str(count))
            
    for it in items:
        if it in dict:
            out = str(dict[it]).replace("\r", "").replace("\n", "\\n").replace(";", "")
            f.write(";\"" + out + "\"")
        else:
            f.write(";")
    f.write("\n")
            
f.flush()

f = open('teilnehmerliste.csv', 'w');

# print header:
f.write("Nachname;Vorname;Ticket;Mi;Do;Fr;T-Shirt;Tagungsband;Dialoge am Inn")
for ws in workshops_sorted:
    f.write(";\"" + str(workshops[ws]) + "\"")
f.write("\n")

# T-Shirt, Tagungsband, Dialoge am Inn
items_sorted = [534,319,316] + workshops_sorted

for person in sorted(persons, key=extractSurname):
    f.write(extractSurname(person) + ";")
    f.write(extractPrename(person) + ";")
    dict = persons[person]
    f.write(extractShortTicketName(items[dict[0]]))
    f.write(" ; ; ;")
            
    for it in items_sorted:
        if it in dict:
            out = str(dict[it]).replace("\r", "").replace("\n", "\\n").replace(";", "")
            f.write(";\"" + out + "\"")
        else:
            f.write(";")
    f.write("\n")
            
f.flush()

for ws in workshops:

    f = open('teilnehmerliste_'+normalize_ws(workshops[ws])+'.csv', 'w');

    # print header:
    f.write(workshops[ws]+"\n")
    f.write("Name;Unterschrift\n")

    for person in sorted(persons, key=extractSurname):
        dict = persons[person]
        if ws in dict:
            f.write(normalize(person + ";\n"))
            
    f.flush()
