#!/usr/bin/env python3
import json
import requests
import os
from bs4 import BeautifulSoup

output_filename = "build-tags.json"

# We locate the table by scanning for "Build" and "Tag" headers.

def fetch_latest_build_tags():
    page = requests.get("https://source.android.com/setup/start/build-numbers")
    soup = BeautifulSoup(page.content, 'html.parser')

    print("Extracting table contents...")
    tags_json = []
    
    tables = soup.find_all('table')
    found_any = False
    for tbl in tables:
        tr = tbl.find('tr')
        if not tr: continue
        headers = [th.get_text().strip() for th in tr.find_all('th')]
        
        if ('Build' in headers or 'Build ID' in headers) and 'Tag' in headers:
            found_any = True
            try:
                for row in tbl.find_all('tr')[1:]:
                    build_json = {}
                    for i, cell in enumerate(row.find_all('td')):
                        key = headers[i]
                        if key == 'Build ID':
                            key = 'Build'
                        # populate the value with "N/A" if no data is available
                        build_json[key] = cell.get_text() if cell.get_text() != '' else 'N/A'
                    if 'Build' in build_json and 'Tag' in build_json:
                        tags_json.append(build_json)
            except:
                print("Unable to extract table contents from a table!")
                continue
                
    if not found_any:
        print("Unable to locate source code tags tables")
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

if __name__ == '__main__':
    fetch_latest_build_tags()