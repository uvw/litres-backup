#!/usr/bin/env python

"""
Very simple tool for backup litres.ru catalog
(c) 2017 kiltum@kiltum.tech
pep8 --ignore=W191,E501 litres-backup.py
for work:
pip install tqdm
"""

import argparse
import os
import time
import xml.etree.ElementTree as ET
from sys import exit

import requests
from tqdm import tqdm

FORMATS = ['fb2.zip', 'html.zip', 'txt.zip', 'rtf.zip', 'fb3', 'a4.pdf', 'a6.pdf', 'mobi.prc', 'epub', 'ios.epub']
URL = "https://robot.litres.ru/pages/"


def main():
    parser = argparse.ArgumentParser(description='litres.ru backup tool')
    parser.add_argument("-u", "--user", default=os.environ.get('LR_USER'), help="Username")
    parser.add_argument("-p", "--password", default=os.environ.get('LR_PASSWORD'), help="Password")
    parser.add_argument("-f", "--format", default="ios.epub", help="Downloading format. 'list' for available")
    parser.add_argument("-d", "--debug", action="store_true", help="Add debug output")
    parser.add_argument("-s", "--size", action="store_true", help="Check file sizes while testing already downloaded books")
    args = parser.parse_args()

    if args.format == 'list':
        for f in FORMATS:
            print(f)
        exit()
    else:
        if args.format not in FORMATS:
            exit(f"Unknown format: {args.format}")

    if str(args.user) == 'None' or str(args.password) == 'None':
        exit("Username or password is missing")

    print(f"Download format: {args.format}")
    print(f"Logging in as: {args.user}")

    r = requests.post(URL + "catalit_authorise/", data={'login': args.user, 'pwd': args.password})
    if args.debug:
        print("Response:", r.status_code, r.reason)
        print("Response text:", r.text)

    root = ET.fromstring(r.text)

    if root.tag == "catalit-authorization-failed":
        exit("Authorization failed")

    sid = root.attrib['sid']

    print(f"Welcome, {root.attrib['login']} ({root.attrib['mail']})")
    print("Querying the list of books (can take some time)...")

    r = requests.post(URL + "catalit_browser/", data={'sid': sid, 'my': "1", 'limit': "0,1000"})

    # if args.debug:
    #    print("Response:", r.status_code, r.reason)
    #    print("Response text:", r.text)

    root = ET.fromstring(r.content)

    count_total = root.attrib['records']
    print(f"Total books: {count_total}")

    if args.debug:
        print(root.tag, root.attrib)

    count = 1

    for child in root:
        if args.debug:
            ET.dump(child)
        hub_id = child.attrib['hub_id']
        file_size = 0
        file_name = child.attrib['filename']
        if not file_name:
            exit("Unable to get the file name")
        file_name = os.path.splitext(file_name)[0] + "." + args.format

        prefix = f"({count} / {count_total}) {file_name}"
        count = count + 1

        for elem in child.iter():
            if elem.tag == 'file' and elem.attrib['type'] == args.format:
                file_size = int(elem.attrib['size'])

        if os.path.exists(file_name):
            existing_size = os.path.getsize(file_name)
            if args.size and existing_size != file_size:
                print(f"{prefix}: file size is different (local={existing_size}, remote={file_size}), downloading again")
                os.remove(file_name)
            else:
                print(f"{prefix}: already exists - skipping")
                continue

        r = requests.post(URL + "catalit_download_book/", data={'sid': sid, 'art': hub_id, 'type': args.format}, stream=True)

        if args.debug:
            print("Response:", r.status_code, r.reason)
            print("Response headers:", r.headers)

        print(prefix)
        with open(file_name, "wb") as file:
            chunks = int(file_size / 1024)
            chunks = chunks if chunks > 0 else 1

            for chunk in tqdm(r.iter_content(chunk_size=1024), unit='kb', total=chunks):
                file.write(chunk)

        time.sleep(1)  # Do not DDoS litres.


if __name__ == "__main__":
    main()
