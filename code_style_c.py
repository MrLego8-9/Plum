#!/usr/bin/python3

import os
import subprocess
import fnmatch
from multiprocessing import Pool, cpu_count


def process_files_chunk(files_chunk):
    vera_results = []
    files_to_check = ("\n".join(files_chunk)).encode('utf-8')
    result = subprocess.run(['vera++', '--profile', 'epitech', '-d'], input=files_to_check, stdout=subprocess.PIPE)
    if result.stdout:
        vera_results = result.stdout.decode('utf-8').strip().split("\n")
    return vera_results


def checkCCodingStyle(ignored_files):
    excluded_dirs = ["./tests", "./bonus", "./.git"]
    excluded_files = [line.strip() for line in ignored_files]

    included_files = []

    for root, dirs, files in os.walk(".", followlinks=True):
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in excluded_dirs]
        for file in files:
            filepath = os.path.join(root, file)
            if not any(fnmatch.fnmatch(filepath, pattern) for pattern in excluded_dirs) and filepath not in excluded_files:
                included_files.append(filepath)

    nb_files = len(included_files)
    num_cores = max(1, min(nb_files // 5, cpu_count()))  # Half the number of CPU cores, but at least 1
    chunk_size = max(1, nb_files // num_cores)

    # Splitting files into chunks
    files_chunks = [included_files[i:i + chunk_size] for i in range(0, len(included_files), chunk_size)]

    # Process each chunk in parallel
    with Pool(processes=num_cores) as pool:
        results = pool.map(process_files_chunk, files_chunks)

    # Flatten the list of results
    vera_result = [item for sublist in results for item in sublist]
    nb_errors = len(vera_result)

    with open("/usr/local/lib/vera++/code_to_comment", "r") as c2c_file:
        c2c = c2c_file.readlines()

    nb_true_errors = nb_errors
    error_count = {"INFO": 0, "MINOR": 0, "MAJOR": 0, "FATAL": 0}
    errors = []
    for i in range(nb_errors):
        special_msg = False
        split_line = vera_result[i].split(":")
        level = split_line[-2].strip(" ")
        if level in ("FATAL", "MAJOR", "MINOR", "INFO"):
            error_count[level] += 1
        split_line[-2] = level

        for rule in c2c:
            if rule.split(":")[0] == split_line[-1]:
                split_line = split_line[:-1] + rule.split(":")
                break

    return error_count, errors
