#!/usr/bin/python3

import os
import sys
import subprocess
import fnmatch


def getIgnoredFiles():
    os.system("git check-ignore $(find . -type f -print) > .plumignore 2> /dev/null")
    with open(".plumignore", "r") as f:
        ignored_files = f.readlines()
    os.system("rm -f .plumignore")
    return [line.replace("\n", "") for line in ignored_files]


def checkCCodingStyle(args):
    ignore_gitignore = "--ignore-gitignore" in args

    excluded_dirs = ["./tests", "./bonus", "./.git"]
    excluded_files = [] if ignore_gitignore else getIgnoredFiles()

    included_files = []

    for root, dirs, files in os.walk(".", followlinks=True):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in excluded_dirs]
        for file in files:
            filepath = os.path.join(root, file)
            # Check if file matches any exclude pattern
            if not any(fnmatch.fnmatch(filepath, pattern) for pattern in excluded_dirs) and filepath not in excluded_files:
                included_files.append(filepath)

    files_to_check = ("\n".join(included_files)).encode('utf-8')

    vera_result = subprocess.run(['vera++', '--profile', 'epitech', '-d'], input=files_to_check, stdout=subprocess.PIPE).stdout.decode('utf-8').split("\n")[:-1]

    with open("/usr/local/lib/vera++/code_to_comment", "r") as c2c_file:
        c2c = c2c_file.readlines()

    nb_errors = len(vera_result)
    for i in range(nb_errors):
        split_line = vera_result[i].split(":")
        if split_line[-2] == " MAJOR":
            split_line[-2] = "\033[91;1m MAJOR\033[0m"
        elif split_line[-2] == " MINOR":
            split_line[-2] = "\033[93;1m MINOR\033[0m"
        elif split_line[-2] == " INFO":
            split_line[-2] = "\033[96;1m INFO\033[0m"
        else:
            split_line[-2] = "\033[90;1m" + split_line[-2] + "\033[0m"

        for rule in c2c:
            if rule.split(":")[0] == split_line[-1]:
                split_line[-1] = ": ".join(rule.split(":"))
                break
        vera_result[i] = ": ".join(split_line)

    return nb_errors, "".join(vera_result)
    #if nb_errors == 0:
    #    print("No errors found")
    #elif nb_errors == 1:
    #    print("\nFound 1 error")
    #else:
    #    print(f"\nFound {nb_errors} errors")