#!/usr/bin/env python3
import argparse
import base64
import json
import os
import requests
from bs4 import BeautifulSoup

script_dir = os.path.dirname(__file__)

output_filename = "project-list.json"
settings_filename = "settings.json"

try:
    settings_path = os.path.join(script_dir, "../config/{}".format(settings_filename))

    settings_file = open(settings_path, 'r')
    settings = json.loads(settings_file.read())
    settings_file.close()
except:
    print("Unable to read {}!".format(settings_filename))
    exit()
    
excluded_projects = settings['settings']['excluded_projects']

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
    project_path = project.get('path')
    if project_path not in excluded_projects:
        projects.append(project_path)

projects_json = {"tag": tag_name, "projects": projects}

print("Saving to '{}'...".format(output_filename))
try:
    output_path = os.path.join(script_dir, "../config/{}".format(output_filename))

    output_file = open(output_path, 'w')
    output_file.write(json.dumps(projects_json, indent=4))
    output_file.close()
except:
    print("Unable to save contents to file!")
    exit()

print("Done!")