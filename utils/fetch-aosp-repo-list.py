#!/usr/bin/env python3
import argparse
import base64
import json
import os
import requests
from bs4 import BeautifulSoup

output_filename = "project-list.json"

parser = argparse.ArgumentParser(description='Fetch a list of project paths for a given AOSP tag')
parser.add_argument('-t', '--tag', help='AOSP tag to pull the manifest for', default='android-10.0.0_r2')
args = parser.parse_args()

manifest_base = "https://android.googlesource.com/platform/manifest"
tag_name = args.tag

print("Fetching manifest for tag '{}'".format(tag_name))

base64_manifest_xml = requests.get("{}/+/refs/heads/{}/default.xml?format=TEXT".format(manifest_base, tag_name))
if base64_manifest_xml.status_code != 200:
    print("Invalid tag specified!")
    exit()

manifest_xml = base64.b64decode(base64_manifest_xml.text)
manifest = BeautifulSoup(manifest_xml, features="html.parser")

# Find all 'project' elements in the manifest
projects = []
for project in manifest.find_all('project'):
    projects.append(project.get('path'))

projects_json = {"tag": tag_name, "projects": projects}

print("Saving to '{}'...".format(output_filename))
try:
    script_dir = os.path.dirname(__file__)
    output_file = os.path.join(script_dir, "../config/{}".format(output_filename))

    f = open(output_file, 'w')
    f.write(json.dumps(projects_json, indent=4))
    f.close()
except:
    print("Unable to save contents to file!")
    exit()

print("Done!")
