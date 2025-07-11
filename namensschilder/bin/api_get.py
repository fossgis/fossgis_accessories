#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Download der Pretix-Daten als JSON nach /namensschilder/data/<EventID>/*.json
"""
import argparse
import datetime
from typing import Union

import requests
import json
import os
from pathlib import Path


def getJsonData(url, filename, headers):
    results = []

    while url:
        print(f'Read {url}')
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}\n\t{response.text}\n\t{response.url}")

        data = response.json()

        results.extend(data.get("results", []))
        url = data['next']

    with open(filename, 'w') as file:
        json.dump(results, file, indent=4, ensure_ascii=False)



def read_pretalx(event_id: str, token: str, dir_output: Union[str, Path]):

    dir_output = Path(dir_output)
    # URL-endpoints
    BASEURL = f"https://pretalx.com/api/events/{event_id}"

    # https://docs.pretix.eu/en/latest/api/resources/orders.html#get--api-v1-organizers-(organizer)-events-(event)-orders-
    TALKS_URL = BASEURL + "/talks/"
    ROOMS_URL = BASEURL + "/rooms/"

    # Auth*
    headers = {
        "Authorization": f"Token {token}"
    }


    # Call the functions to execute the code
    getJsonData(ROOMS_URL, dir_output / "pretalx_rooms.json", headers)
    getJsonData(TALKS_URL, dir_output / "pretalx_talks.json", headers)


def read_pretix(event_id: str, token: str, dir_output: Union[str, Path]):

    dir_output = Path(dir_output)
    # URL-endpoints
    BASEURL = f"https://pretix.eu/api/v1/organizers/fossgis/events/{event_id}"

    # https://docs.pretix.eu/en/latest/api/resources/orders.html#get--api-v1-organizers-(organizer)-events-(event)-orders-
    ORDER_URL = BASEURL + "/orders/"
    # https://docs.pretix.eu/en/latest/api/resources/invoices.html#get--api-v1-organizers-(organizer)-events-(event)-invoices-
    INVOICE_URL = BASEURL + "/invoices/"
    # ?????????????????
    NREI_URL = BASEURL + "/orders?identifier=dekodi_nrei"
    # https://docs.pretix.eu/en/latest/api/resources/items.html#get--api-v1-organizers-(organizer)-events-(event)-items-
    ITEMS_URL = BASEURL + "/items/"

    ITEM_CATEGORY_URL = BASEURL + "/categories/"

    QUESTIONS = BASEURL + "/questions/"


    # Auth*
    headers = {
        "Authorization": f"Token {token}"
    }


    # Call the functions to execute the code

    getJsonData(QUESTIONS, dir_output / "pretix_questions.json", headers)
    getJsonData(ITEM_CATEGORY_URL, dir_output / "pretix_categories.json", headers)
    getJsonData(ORDER_URL, dir_output / "pretix_orders.json", headers)
    getJsonData(ITEMS_URL, dir_output / "pretix_items.json", headers)
    # getJsonData(INVOICE_URL, dir_output / "pretix_invoices.json", headers)
    # getJsonData(NREI_URL, root / "pretix_nrei.json", headers)



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Download der Pretix- & Pretalx-Daten als JSON '
                                                 'zur weiteren Verarbeitung')
    parser.add_argument('-o', '--output',
                        type=str,
                        default=Path(__file__).parents[1] / "json" ,
                        help='Ausgabeordner für die JSON-Dateien')
    parser.add_argument('-y', '--year',
                        type=int,
                        default=datetime.date.today().year,
                        help='Jahr der FOSSGIS')
    parser.add_argument('--pretix',
                        required=False,
                        default=None,
                        help='Pretix API Token (https://docs.pretix.eu/en/latest/api/auth.html)',
                        action='store_true')
    parser.add_argument('--pretalx',
                        required=False,
                        default=None,
                        help='Pretalx API Token (https://docs.pretalx.org/api/fundamentals/#obtaining-an-api-token)',
                        action='store_true')


    args = parser.parse_args()

    dir_output = Path(args.output)
    os.makedirs(dir_output, exist_ok=True)

    pretix_token = args.pretix
    pretalx_token = args.pretalx
    if pretix_token is None:
        pretix_token = os.environ.get('PRETIX_TOKEN')

    if pretalx_token is None:
        pretalx_token = os.environ.get('PRETALX_TOKEN')

    if pretix_token is None and pretalx_token is None:
        raise ValueError('Es wurde weder ein Pretix- noch ein Pretalx-Token angegeben')

    if False and pretalx_token:
        event_id = f'fossgis{args.year}'
        read_pretalx(event_id, pretalx_token, dir_output)

    if pretix_token:
        event_id = f'{args.year}'
        read_pretix(event_id, pretix_token, dir_output)



