#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import shutil
import time
import xml.etree.ElementTree as ET

def execute_with_retry(func, *args, retries=3, delay=5, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            if attempt < retries - 1:
                print("Command failed! Retrying in {} seconds... ({}/{})".format(delay, attempt + 1, retries))
                time.sleep(delay)
            else:
                raise e

def create_gh_repo(working_path, repository_name):
    try:
        subprocess.check_output(["gh", "repo", "create", repository_name, "--private"], stderr=subprocess.STDOUT, cwd=working_path)
    except subprocess.CalledProcessError as e:
        output = e.output.decode('utf-8', errors='ignore')
        if "Name already exists" in output:
            print("Repository {} already exists. Skipping creation.".format(repository_name))
        else:
            raise e

def git(*args, working_path=""):
    args_list = ("-C", working_path) + args
    return subprocess.check_output(['git'] + list(args_list))

def main():
    parser = argparse.ArgumentParser(description="Generate and push a custom AOSP manifest overlaying modified forks")
    parser.add_argument('-r', '--results', help='Path to results.json from splitter.py', required=True)
    parser.add_argument('-b', '--branch', help='Branch name to push the manifest to', required=True)
    parser.add_argument('-o', '--organization', help='GitHub Organization', required=True)
    parser.add_argument('-c', '--commit', help='Commit message', default='Add Custom Manifest')
    parser.add_argument('-w', '--working', help='Temporary working directory', default='/tmp/manifest-generator')
    args = parser.parse_args()

    # Load results.json
    try:
        with open(args.results, 'r') as f:
            results = json.load(f)
    except Exception as e:
        print("Failed to load results file:", e)
        exit(1)

    tag = results.get("info", {}).get("tag")
    if not tag:
        print("Results JSON does not contain a valid tag in 'info' object!")
        exit(1)

    modified_projects = results.get("modified", [])
    if not modified_projects:
        print("No modified projects found in results.json!")

    working_path = args.working
    if not working_path.endswith('/'):
        working_path += '/'

    if os.path.exists(working_path):
        shutil.rmtree(working_path)
    os.makedirs(working_path)

    print("Cloning platform/manifest using tag {}...".format(tag))
    git("init", working_path=working_path)
    git("remote", "add", "google", "https://android.googlesource.com/platform/manifest", working_path=working_path)
    try:
        execute_with_retry(git, "fetch", "google", working_path=working_path)
    except subprocess.CalledProcessError:
        print("Failed to fetch platform/manifest")
        exit(1)

    git("checkout", "tags/{}".format(tag), "-b", args.branch, working_path=working_path)

    # Parse XML
    manifest_xml_path = os.path.join(working_path, "default.xml")
    if not os.path.exists(manifest_xml_path):
        print("default.xml not found in manifest repo!")
        exit(1)

    print("Modifying default.xml...")
    import re
    
    with open(manifest_xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add <remote> element for GitHub if doesn't exist
    if '<remote name="github"' not in content:
        # Try to insert before <default
        content = re.sub(
            r'(\n\s*)(<default\s)', 
            r'\1<remote name="github" fetch="git@github.com:{}/" />\1\2'.format(args.organization), 
            content, 
            count=1
        )
        # Fallback if no <default found
        if '<remote name="github"' not in content:
            content = re.sub(
                r'(<manifest>\n)', 
                r'\1  <remote name="github" fetch="git@github.com:{}/" />\n'.format(args.organization),
                content,
                count=1
            )

    # Modify matching projects
    for p in modified_projects:
        pattern = r'(<project\s+[^>]*?path=[\'"]{}[\'"][^>]*>)'.format(re.escape(p))
        
        def attr_replacer(match):
            tag = match.group(1)
            p_name = "android_{}".format(p.replace("/", "_"))
            
            # Replace existing name, or append if missing
            if re.search(r'\s+name=[\'"][^\'"]*[\'"]', tag):
                tag = re.sub(r'(\s+name=)[\'"][^\'"]*[\'"]', r'\g<1>"{}"'.format(p_name), tag)
            else:
                tag = re.sub(r'\s*/>$', ' name="{}" />'.format(p_name), tag) if tag.endswith('/>') else re.sub(r'\s*>$', ' name="{}">'.format(p_name), tag)

            # Replace existing remote, or append
            if re.search(r'\s+remote=[\'"][^\'"]*[\'"]', tag):
                tag = re.sub(r'(\s+remote=)[\'"][^\'"]*[\'"]', r'\g<1>"github"', tag)
            else:
                tag = re.sub(r'\s*/>$', ' remote="github" />', tag) if tag.endswith('/>') else re.sub(r'\s*>$', ' remote="github">', tag)
                
            # Replace existing revision, or append
            if re.search(r'\s+revision=[\'"][^\'"]*[\'"]', tag):
                tag = re.sub(r'(\s+revision=)[\'"][^\'"]*[\'"]', r'\g<1>"{}"'.format(args.branch), tag)
            else:
                tag = re.sub(r'\s*/>$', ' revision="{}" />'.format(args.branch), tag) if tag.endswith('/>') else re.sub(r'\s*>$', ' revision="{}">'.format(args.branch), tag)
                
            return tag
            
        content = re.sub(pattern, attr_replacer, content)

    # Write modified XML back
    with open(manifest_xml_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Commit and Push
    if git("status", "-s", working_path=working_path) == b'':
        print("No changes needed in manifest.")
        shutil.rmtree(working_path)
        return
        
    git("add", "default.xml", working_path=working_path)
    git("commit", "-m", args.commit, working_path=working_path)

    repository_name = "{}/android_manifest".format(args.organization)
    print("Creating repository {}...".format(repository_name))
    try:
        execute_with_retry(create_gh_repo, working_path, repository_name)
    except subprocess.CalledProcessError as e:
        output = e.output.decode('utf-8', errors='ignore') if hasattr(e, 'output') and e.output else str(e)
        print("Failed to create repository {}! Error: {}".format(repository_name, output))
        exit(1)

    try:
        git("remote", "add", "origin", "git@github.com:{}.git".format(repository_name), working_path=working_path)
    except subprocess.CalledProcessError:
        pass # Remote might already exist

    print("Pushing custom manifest...")
    try:
        execute_with_retry(git, "push", "-f", "origin", args.branch, working_path=working_path)
    except subprocess.CalledProcessError:
        print("Push rejected!")
        exit(1)

    print("Successfully published custom manifest to {}!".format(repository_name))
    shutil.rmtree(working_path)

if __name__ == '__main__':
    main()
