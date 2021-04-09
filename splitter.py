#!/usr/bin/env python3
import argparse
from datetime import datetime
import glob
import importlib
import json
import os
import subprocess
import shutil
import utils.fetch_aosp_build_tags as tags_helper
import utils.fetch_aosp_repo_list as repo_helper

script_dir = os.path.dirname(__file__)

req_modules = ["bs4", "requests"]
req_tools = ["hub", "git"]

def read_config(filename):
    try:
        path = os.path.join(script_dir, "./config/{}".format(filename))

        file = open(path, 'r')
        output = json.loads(file.read())
        file.close()
        return output
    except:
        print("Unable to read {}!".format(filename))
        exit()

settings = read_config("settings.json")["settings"]
parser = argparse.ArgumentParser(description="Merge a BSP with the closest matching AOSP tag we're able to find",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-r', '--refresh', help='Force a refresh of the latest AOSP build tags from Google', action='store_true')
parser.add_argument('-p', '--path', help='Path at which the BSP is located', required=True)
# These values are optional, and will default to the corresponding values in settings.json
parser.add_argument('-w', '--working', help='Path to a temporary working directory', default=settings["tmp_directory"])
parser.add_argument('-b', '--branch', help='Branch name to use for the changes', default=settings["branch_name"])
parser.add_argument('-o', '--organization', help='Organization name to use for pushing the repositories to', default=settings["org_name"])
parser.add_argument('-c', '--commit', help='Commit message to use when committing the BSP changes', default=settings["commit_message"])
args = parser.parse_args()

force_tags_refresh = args.refresh
bsp_path = args.path
if (not bsp_path.endswith("/")):
    bsp_path += "/"
working_path = args.working
if (not working_path.endswith("/")):
    working_path += "/"
branch_name = args.branch
org_name = args.organization
commit_message = args.commit

bsp_migration_results_json = {}

def check_modules():
    for module in req_modules:
        if (importlib.util.find_spec(module) is None):
            print(("It looks like you don't have the '{}' Python module installed. \n"
                "Please run the following command then try running this script again:\n\n"
                "pip3 install -r requirements.txt\n").format(module))
            exit()

def check_tools():
    for tool in req_tools:
        if (shutil.which(tool) is None):
            print(("It looks like you don't have the '{}' tool installed. "
                "Please install '{}' and try again.").format(tool, tool));
            exit()

def print_build_info(build):
    print("    Build ID: {}".format(build["Build"]))
    print("    Build Tag: {}".format(build["Tag"]))
    print("    Build Version: {}".format(build["Version"]))
    print("    Security Patch Level: {}".format(build["Security patch level"]))

def get_bsp_build_id(bsp_path):
    build_id_file = "build/make/core/build_id.mk"
    build_id_text = "BUILD_ID="
    
    if (not bsp_path.endswith("/")):
        bsp_path += "/"
        
    try:
        bsp_build_id_file = open(bsp_path + build_id_file, "r")
    except FileNotFoundError:
        print("Could not read from file {}, please make sure the BSP is complete."
            .format(bsp_path + build_id_file))
        exit()
    for line in bsp_build_id_file.readlines():
        if (line.startswith(build_id_text)):
            bsp_build_id_file.close()
            bsp_build_id = line.rstrip().replace(build_id_text, "")
            print("BSP has BUILD_ID of {}".format(bsp_build_id))
            return bsp_build_id
    print("String '{}' not found in file at {}. Please make sure the BSP is complete."
        .format(build_id_text, bsp_path + build_id_file))
    exit()

def get_tag_for_build_id(build_id):
    build_tags = read_config("build-tags.json")
    for build in build_tags:
        if (build["Build"] == build_id):
            print("Found build info matching Build ID {}".format(build_id))
            print_build_info(build)
            return build["Tag"]

def get_origin_path_for_project(project):
    origin_path_replacements = settings["project_origin_replacements"]
    for replacement in origin_path_replacements:
        if project.startswith(replacement):
            return origin_path_replacements[replacement].replace("{project}", project)
    print("No rule found that matches project '{}'! Please add one to settings.json".format(project))
    exit()

def git(*args):
    # The command "git -C dirname status" will cd to dirname before running "git status"
    args = ("-C", working_path) + args
    return subprocess.check_output(['git'] + list(args))

def copy_bsp_project_to_tmp_folder(project_path, tmp_folder):
    for item in glob.glob(tmp_folder + "*"):
        if ".git" not in item:    
            os.system("rm -rf {}".format(item))
    os.system("cp -rf {}/* {}".format(project_path, tmp_folder))

if __name__ == '__main__':
    check_modules()
    check_tools()
    if (force_tags_refresh):
        tags_helper.fetch_latest_build_tags()
    
    build_id = get_bsp_build_id(bsp_path)
    build_tag = get_tag_for_build_id(build_id)
    bsp_migration_results_json["info"] = {"build_id": build_id, "tag": build_tag, "path": bsp_path}
    projects = repo_helper.fetch_manifest_for_tag(build_tag)["projects"]
    
    modified = []
    no_changes = []
    not_found = []
    failed = []
    
    for project in projects:
        local_project_path = bsp_path + project
        
        if (os.path.exists(local_project_path) and os.path.isdir(local_project_path)):
            print("Processing {}...".format(project))
            corrected_origin_path = get_origin_path_for_project(project)
        
            if (os.path.exists(local_project_path + "/.git")):
                print("Project {} has a .git folder, marking as failed.".format(project))
                failed.append(project)
                continue

            if (os.path.exists(working_path)):
                shutil.rmtree(working_path)

            try:
                os.mkdir(working_path)
            except OSError:
                print("Failed to create temporary directory {}".format(working_path))

            git("init")
            git("remote", "add", "google", "https://android.googlesource.com/{}".format(corrected_origin_path))
            git("fetch", "google")
            git("checkout", "tags/{}".format(build_tag), "-b", branch_name)
            git("config", "core.filemode", "false")

            copy_bsp_project_to_tmp_folder(local_project_path, working_path)
            
            if (git("status", "-s") == b''):
                print("No changes in {}.".format(project))
                no_changes.append(project)
            else:
                git("add", "--all")
                git("commit", "-m", commit_message)
                repository_name = "{}/android_{}".format(org_name, project.replace("/", "_"))
                print("Pushing to {}...".format(repository_name))
                os.system("cd {}; hub create {}".format(working_path, repository_name))
                git("push", "-f", "origin", branch_name)
                print("Pushed changes for {}".format(project))
                modified.append(project)

            shutil.rmtree(working_path)
        else:
            print("Project '{}' from projects list not found in BSP.".format(project))
            not_found.append(project)

    bsp_migration_results_json["modified"] = modified
    bsp_migration_results_json["no_changes"] = no_changes
    bsp_migration_results_json["not_found"] = not_found
    bsp_migration_results_json["failed"] = failed
    
    results_filename = "results_{}.json".format(datetime.now().strftime('%Y%m%d-%H%M%S'))
    print("Saving to '{}'...".format(results_filename))
    try:
        script_dir = os.path.dirname(__file__)
        results_file = os.path.join(script_dir, "./output/{}".format(results_filename))

        f = open(results_file, 'w')
        f.write(json.dumps(bsp_migration_results_json, indent=4))
        f.close()
    except:
        print("Unable to save contents to file!")
        exit()
    print("Done!")
