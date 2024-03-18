#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import json

# URL-endpoints
BASEURL = "https://pretix.eu/api/v1/organizers/fossgis/events/"
EVENT_ID = "demo-2020"
# https://docs.pretix.eu/en/latest/api/resources/orders.html#get--api-v1-organizers-(organizer)-events-(event)-orders-
ORDER_URL = BASEURL + EVENT_ID + "/orders/"
# https://docs.pretix.eu/en/latest/api/resources/invoices.html#get--api-v1-organizers-(organizer)-events-(event)-invoices-
INVOICE_URL = BASEURL + EVENT_ID + "/invoices/"
# ?????????????????
NREI_URL = BASEURL + EVENT_ID + "/orders?identifier=dekodi_nrei"
# https://docs.pretix.eu/en/latest/api/resources/items.html#get--api-v1-organizers-(organizer)-events-(event)-items-
ITEMS_URL = BASEURL + EVENT_ID + "/items/"

# Auth*
headers = {
    "Authorization": "Token INSERTTOKENHERE"
}


def getOrders():
    # Get orders
    orders = requests.get(ORDER_URL, headers=headers)
    order_data = orders.json().get("results", [])

    # Save orders to a file
    with open("./data/orders.json", "w") as orders_file:
        json.dump(order_data, orders_file, indent=4)


def getInvoices():
    # Get invoices
    invoices = requests.get(INVOICE_URL, headers=headers)
    invoice_data = invoices.json().get("results", [])

    # Save invoices to a file
    with open("./data/invoices.json", "w") as invoices_file:
        json.dump(invoice_data, invoices_file, indent=4)


def getNREI():
    # Get nrei
    nrei = requests.get(NREI_URL, headers=headers)
    nrei_data = nrei.json().get("results", [])

    # Save nrei to a file
    with open("./data/nrei.json", "w") as nrei_file:
        json.dump(nrei_data, nrei_file, indent=4)


def getItems():
    # Get items/products
    items = requests.get(ITEMS_URL, headers=headers)
    items_data = items.json().get("results", [])

    # Save items to a file
    with open("./data/items.json", "w") as items_file:
        json.dump(items_data, items_file, indent=4)


# Call the functions to execute the code
getOrders()
getInvoices()
getNREI()
getItems()
