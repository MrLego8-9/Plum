#!/usr/bin/python3

from code_style_c import checkCCodingStyle
from code_style_haskell import checkHaskellCodingStyle
import os

FATAL_COLOR = "\033[91;1;4m"
MAJOR_COLOR = "\033[91;1m"
MINOR_COLOR = "\033[93;1m"
INFO_COLOR = "\033[96;1m"
TITLE_COLOR = "\033[1m"
SPECIAL_COLOR = "\033[94;1m"
FILE_COLOR = "\033[90m"
OK_COLOR = "\033[92m"
NO_COLOR = "\033[0m"

colors_dict = {"FATAL": FATAL_COLOR, "MAJOR": MAJOR_COLOR, "MINOR": MINOR_COLOR, "INFO": INFO_COLOR}


def getIgnoredFiles() -> list[str]:
    try:
        os.system("git check-ignore $(find . -type f -print) > .plumgitignore 2> /dev/null")
        with open(".plumgitignore", "r") as f:
            ignored_git_files = f.readlines()
        os.system("rm -f .plumgitignore")
    except:
        ignored_git_files = []
    try:
        with open(".plumignore", "r") as f:
            ignored_plum_files = f.readlines()
    except FileNotFoundError:
        ignored_plum_files = []
    return ignored_git_files + ignored_plum_files


def getErrorsDict(errors: list) -> dict:
    errors_dict = {}
    for error in errors:
        if errors_dict.get(error[0]) is None:
            errors_dict[error[0]] = [error[1:]]
        else:
            errors_dict[error[0]] += [error[1:]]
    return errors_dict


def printError(file: str, tokens: list):
    print("   ", end='')
    if len(tokens) == 1:
        print(f"{SPECIAL_COLOR}[SPECIAL]{NO_COLOR} - {tokens[0]} {FILE_COLOR}({file}){NO_COLOR}")
        return
    tokens[-1] = tokens[-1].strip("\n")
    if tokens[1] in ("FATAL", "MAJOR", "MINOR", "INFO"):
        print(f"{colors_dict[tokens[1]]}[{tokens[1]}] ({tokens[2]}){NO_COLOR} - {tokens[3]} {FILE_COLOR}({file}:{tokens[0]}){NO_COLOR}")
    else:
        line = tokens[0]
        text = ''.join(tokens[1:])
        print(f"{SPECIAL_COLOR}[SPECIAL]{NO_COLOR} - {text} {FILE_COLOR}({file}:{line}){NO_COLOR}")


def printReport(report: dict):
    print(f"{FATAL_COLOR}[FATAL]{NO_COLOR} : {report['FATAL']} | ", end='')
    print(f"{MAJOR_COLOR}[MAJOR]{NO_COLOR} : {report['MAJOR']} | ", end='')
    print(f"{MINOR_COLOR}[MINOR]{NO_COLOR} : {report['MINOR']} | ", end='')
    print(f"{INFO_COLOR}[INFO]{NO_COLOR} : {report['INFO']}")


def runChecks(args):
    ignored_files = []
    if not args.ignoregitignore:
        ignored_files = getIgnoredFiles()
    c_results = checkCCodingStyle(ignored_files)
    haskell_results = checkHaskellCodingStyle(ignored_files)

    c_error_sum = sum(c_results[0].values())
    haskell_error_sum = sum(haskell_results[0].values())

    global_error_sum = c_error_sum + haskell_error_sum
    c_errors = getErrorsDict(c_results[1])
    haskell_errors = getErrorsDict(haskell_results[1])
    if c_error_sum > 0:
        print("\n\033[96;1mC Style results\033[0m\n")
        for file, errors in c_errors.items():
            sorted_errors = sorted(errors, key=(lambda x: x[0]))
            print(f"\n{TITLE_COLOR}‣ In File {file}{NO_COLOR}")
            for error in sorted_errors:
                printError(file, error)

    if haskell_error_sum > 0:
        print("\n\033[96;1mHaskell Style results\033[0m\n")
        for file, errors in haskell_errors.items():
            sorted_errors = sorted(errors, key=(lambda x: x[0]))
            print(f"\n{TITLE_COLOR}‣ In File {file}{NO_COLOR}")
            for error in sorted_errors:
                printError(file, error)

    if global_error_sum == 0:
        print(f"{OK_COLOR}No errors found{NO_COLOR}")
        exit(0)

    if c_error_sum > 0:
        print(f"\n{TITLE_COLOR}C report:{NO_COLOR}")
        printReport(c_results[0])
    if haskell_error_sum > 0:
        print(f"\n{TITLE_COLOR}Haskell report:{NO_COLOR}")
        printReport(haskell_results[0])
    global_errors = {}
    for key in c_results[0].keys():
        global_errors[key] = c_results[0][key] + haskell_results[0][key]
    print(f"\n{TITLE_COLOR}Global report:{NO_COLOR}")
    printReport(global_errors)
    exit(0 if args.nostatus else 1)

