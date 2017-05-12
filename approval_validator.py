#!/usr/bin/python

import sys, os
import argparse
from pathlib import Path
from collections import defaultdict


# Constants
CURRENT_WORKING_DIRECTORY = os.getcwd()
ROOT = CURRENT_WORKING_DIRECTORY + '/repo_root/'
OWNERS = '/OWNERS'
DEPENDENCIES = '/DEPENDENCIES'
APPROVED = 'Approved'
NOT_APPROVED = 'Insufficient Approvals'


def read_file(file_path):
    with open(str(file_path), 'r') as data:
        return [line.strip() for line in data.readlines()]


#   Creates a map of all dependencies for the given repository
#   { key : [value] } where "value" is a list of directories dependent on "key"
#   That is, for each directory A, finds all the [directories] that are dependent on A
def build_dependency_map(root_directory):
    dependency_map = defaultdict(list)
    for root, dirs, files in os.walk(root_directory):
        current_dir = os.path.basename(root)         # subdirs : follow, message, tweet, or user
        dependency_file = Path(root_directory + current_dir + DEPENDENCIES)           # path of file
        dependency_data = read_file(dependency_file) if dependency_file.exists() else None
        if dependency_data is None:
            continue
        #add dependencies to the map
        for dependency in range(len(dependency_data)):
            dependency_map.setdefault(dependency_data[dependency], []).append(root_directory + current_dir)
    return dependency_map


#   Checks if even one of the approvers is the owner of the directory
#   If owners file doesn't exist, function checks it in the parent directory of the current directory
def check_owners(approvers, directory_path):
    #if there is no owner till the repo's root directory for a file,
    #then assume user has the right to approve that file and return true
    if directory_path == CURRENT_WORKING_DIRECTORY:
        return True
    owners_file = Path(str(directory_path) + OWNERS)
    owners = read_file(owners_file) if owners_file.exists() else None
    result = False
    #if any of the approvers is an owner then return true
    if owners:
        for owner in range(len(owners)):
            if owners[owner] in approvers:
                return True
        return False
    #if owners file doesn't exist in this directory, check parent
    else:
        result = check_owners(approvers, os.path.dirname(str(directory_path)))
    return result


#   If any directory is dependent on the given directory, check approvers for the dependent dirs
def check_dependencies(approvers, directory_path):
    dependency_map = defaultdict(list)
    dependency_map = build_dependency_map(ROOT + 'src/com/twitter/')
    dependency_list = []
    if directory_path in dependency_map:
        dependency_list = dependency_map[directory_path]
        for dependency in range(len(dependency_list)):
            if validate_approval(approvers, dependency_list[dependency]) == False:
                return False
    return True


#   Returns Approved if sufficient approvals were provided
#   Returns Not Approved otherwise
def validate_approval(approvers, files_changed):
    for file in range(len(files_changed)):
        directory_path = Path(ROOT + os.path.dirname(files_changed[file]))
        if check_owners(approvers, directory_path) == False:
            return NOT_APPROVED
        if check_dependencies(approvers, directory_path) == False:
            return NOT_APPROVED
    return APPROVED


#   main() parses the user input and calls validate_approval()
def main():
    parser = argparse.ArgumentParser(prog='validate_approvals', description='This command validates if correct people have approved the changes made to a set of files')
    requiredArgs = parser.add_argument_group('Required Arguments')
    requiredArgs.add_argument('--approvers', help='List all approver names separated by space', required=True, action='store',type=str,nargs='*')
    requiredArgs.add_argument('--changed-files', help='List path of all files that have been modified', required=True, action='store',type=str,nargs='*')
    args = parser.parse_args()
    print (validate_approval(args.approvers, args.changed_files))

main()
