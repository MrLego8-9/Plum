#!/usr/bin/python3
import subprocess


def checkHaskellCodingStyle(ignored_files):
    gitignore_content = ":".join(line.rstrip("\n").lstrip("./") for line in ignored_files)
    excluded_files = ("Setup.hs:setup.hs:.git:.stack-work:test:tests:bonus" + gitignore_content).strip(':')

    vera_result = subprocess.run(['lambdananas', '-o', 'vera', '--exclude', excluded_files, '.'],
                                 stdout=subprocess.PIPE).stdout.decode('utf-8').split("\n")[:-1]

    nb_errors = len(vera_result)
    error_count = {"INFO": 0, "MINOR": 0, "MAJOR": 0, "FATAL": 0}
    errors = []

    for i in range(nb_errors):
        split_line = vera_result[i].split(":")
        if len(split_line) != 4:
            sl = vera_result[i].split(" ")
            errors.append([sl[0], vera_result[i]])
            continue
        level = split_line[-2].strip(" ")
        if level in ("FATAL", "MAJOR", "MINOR", "INFO"):
            error_count[level] += 1
        split_line[-2] = level
        split_line = split_line[:-1] + [part.strip(" ") for part in split_line[-1].split("#")]
        errors.append(split_line)
    return error_count, errors
