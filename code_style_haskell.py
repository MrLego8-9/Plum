#!/usr/bin/python3

import os
import sys
import subprocess

def getIgnoredFiles():
    os.system("git check-ignore $(find . -type f -print) > .plumgitignore 2> /dev/null")
    with open(".plumgitignore", "r") as f:
        ignored_git_files = f.readlines()
    os.system("rm -f .plumgitignore")
    with open(".plumignore", "r") as f:
        ignored_plum_files = f.readlines()
    return ":".join(line.rstrip("\n").lstrip("./") for line in (ignored_plum_files + ignored_git_files))


def checkHaskellCodingStyle(args):
    ignore_gitignore = "--ignore-gitignore" in args

    gitignore_content = getIgnoredFiles() if ignore_gitignore else ""
    excluded_files = ("Setup.hs:setup.hs:.git:.stack-work:test:tests:bonus" + gitignore_content).strip(':')

    vera_result = subprocess.run(['lambdananas', '-o', 'vera', '--exclude', excluded_files, '.'], stdout=subprocess.PIPE).stdout.decode('utf-8').split("\n")[:-1]

    nb_errors = len(vera_result)
    for i in range(nb_errors):
        split_line = vera_result[i].split(":")
        if split_line[-2] == " MAJOR":
            split_line[-2] = "\033[91;1mMAJOR\033[0m"
        elif split_line[-2] == " MINOR":
            split_line[-2] = "\033[93;1mMINOR\033[0m"
        elif split_line[-2] == " INFO":
            split_line[-2] = "\033[96;1mINFO\033[0m"
        else:
            split_line[-2] = "\033[90;1m" + split_line[-2] + "\033[0m"

        vera_result[i] = ": ".join(split_line) + "\n"

    return nb_errors, "".join(vera_result), nb_errors != 0
    #if nb_errors == 0:
    #    print("No errors found")
    #elif nb_errors == 1:
    #    print("\nFound 1 error")
    #else:
    #    print(f"\nFound {nb_errors} errors")
