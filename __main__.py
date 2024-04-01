#!/usr/bin/python3
import argparse
import os
from code_style_checker import runChecks

parser = argparse.ArgumentParser()
parser.add_argument("--update", help="Update Plum", action="store_true", dest="updaterules")
parser.add_argument("--update-rules", help="Update the coding style rules", action="store_true")
parser.add_argument("--ignore-gitignore", help="Do not ignore files in .gitignore and .plumignore", action="store_true", dest="ignoregitignore")
parser.add_argument("--no-status", help="Always exit with code 0", action="store_true", dest="nostatus")

args = parser.parse_args()

if args.update:
    os.system("/opt/plum-coding-style/plum_update.sh")
    exit(0)

if args.updaterules:
    os.system("/opt/plum-coding-style/plum_update.sh --update-rules")
    exit(0)

runChecks(args)
