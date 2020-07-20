#!/usr/bin/env python3
import json
import requests
import os
from bs4 import BeautifulSoup

output_filename = "build-tags.json"

page = requests.get("https://source.android.com/setup/start/build-numbers")
soup = BeautifulSoup(page.content, 'html.parser')

try:
    table = soup.select("#source-code-tags-and-builds ~ p > table")[0]
except:
    print("Unable to locate source code tags table")
    exit()

tags_json = []

# Get table headers
print("Extracting table headers...")
try:
    headers = table.find('tr').find_all('th')
    for i,header in enumerate(headers):
        headers[i] = header.get_text()
except:
    print("Unable to extract table headers!")
    exit()

# Get all non-header table rows
print("Extracting table contents...")
try:
    for row in table.find_all('tr')[1:]:
        build_json = {}
        for i,cell in enumerate(row.find_all('td')):
            # populate the value with "N/A" if no data is available
            build_json[headers[i]] = cell.get_text() if cell.get_text() != '' else 'N/A'
        tags_json.append(build_json)
except:
    print("Unable to extract table contents!")
    exit()

print("Saving to '{}'...".format(output_filename))
try:
    script_dir = os.path.dirname(__file__)
    output_file = os.path.join(script_dir, "../config/{}".format(output_filename))

    f = open(output_file, 'w')
    f.write(json.dumps(tags_json, indent=4))
    f.close()
except:
    print("Unable to save contents to file!")
    exit()

print("Done!")
