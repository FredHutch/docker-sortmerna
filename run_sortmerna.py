#!/usr/bin/env python3
"""Filter a set of reads with SortMeRNA."""

import os
import sys
import time
import json
import uuid
import shutil
import logging
import argparse
import traceback
import subprocess


def exit_and_clean_up(temp_folder):
    """Log the error messages and delete the temporary folder."""
    # Capture the traceback
    logging.info("There was an unexpected failure")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    for line in traceback.format_tb(exc_traceback):
        logging.info(line)

    # Delete any files that were created for this sample
    logging.info("Removing temporary folder: " + temp_folder)
    shutil.rmtree(temp_folder)

    # Exit
    logging.info("Exit type: {}".format(exc_type))
    logging.info("Exit code: {}".format(exc_value))
    sys.exit(exc_value)


def run_cmds(commands, retry=0, catchExcept=False):
    """Run commands and write out the log, combining STDOUT & STDERR."""
    logging.info("Commands:")
    logging.info(' '.join(commands))
    p = subprocess.Popen(commands,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    stdout, stderr = p.communicate()
    exitcode = p.wait()
    if stdout:
        logging.info("Standard output of subprocess:")
        for line in stdout.split('\n'):
            logging.info(line)
    if stderr:
        logging.info("Standard error of subprocess:")
        for line in stderr.split('\n'):
            logging.info(line)

    # Check the exit code
    if exitcode != 0 and retry > 0:
        msg = "Exit code {}, retrying {} more times".format(exitcode, retry)
        logging.info(msg)
        run_cmds(commands, retry=retry - 1)
    elif exitcode != 0 and catchExcept:
        msg = "Exit code was {}, but we will continue anyway"
        logging.info(msg.format(exitcode))
    else:
        assert exitcode == 0, "Exit code {}".format(exitcode)


def get_file_from_url(input_str, temp_folder):
    """Get a file from a URL -- return the downloaded filepath."""
    logging.info("Getting file from {}".format(input_str))

    filename = input_str.split('/')[-1]
    local_path = os.path.join(temp_folder, filename)

    logging.info("Filename: " + filename)
    logging.info("Local path: " + local_path)

    if not input_str.startswith(('s3://', 'ftp://')):
        logging.info("Treating as local path")
        msg = "Input file does not exist ({})".format(input_str)
        assert os.path.exists(input_str), msg
        logging.info("Making symbolic link in temporary folder")
        os.symlink(input_str, local_path)
        return local_path

    # Get files from AWS S3
    if input_str.startswith('s3://'):
        logging.info("Getting reads from S3")
        run_cmds([
            'aws', 's3', 'cp', '--quiet', '--sse',
            'AES256', input_str, temp_folder
            ])

    # Get files from an FTP server
    elif input_str.startswith('ftp://'):
        logging.info("Getting reads from FTP")
        run_cmds(['wget', '-P', temp_folder, input_str])

    else:
        raise Exception("Did not recognize prefix to fetch file: " + input_str)

    return local_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    Filter a set of reads with SortMeRNA.
    """)

    parser.add_argument("--input",
                        type=str,
                        required=True,
                        help="""Location for input file.
                                (Supported: local path, s3://, or ftp://).""")
    parser.add_argument("--output-reads",
                        type=str,
                        required=True,
                        help="""Path for output reads.""")
    parser.add_argument("--output-logs",
                        type=str,
                        required=True,
                        help="""Path for output logs.""")
    parser.add_argument("--db",
                        type=str,
                        default="/usr/sortmerna/sortmerna-2.1b/rRNA_databases/all_rRNA-db",
                        help="""Path for database.""")
    parser.add_argument("--threads",
                        type=int,
                        default=1,
                        help="""Number of threads to use for alignment.""")
    parser.add_argument("--temp-folder",
                        type=str,
                        default='/share',
                        help="Folder used for temporary files.")

    args = parser.parse_args()

    # Check that the temporary folder exists
    assert os.path.exists(args.temp_folder)

    # Set a random string, which will be appended to all temporary files
    random_string = str(uuid.uuid4())[:8]

    # Make a temporary folder within the --temp-folder with the random string
    temp_folder = os.path.join(args.temp_folder, str(random_string))
    # Make sure it doesn't already exist
    msg = "Collision, {} already exists".format(temp_folder)
    assert os.path.exists(temp_folder) is False, msg
    # Make the directory
    os.mkdir(temp_folder)

    # Set up logging
    log_fp = '{}/log.txt'.format(temp_folder)
    logFormatter = logging.Formatter('%(asctime)s %(levelname)-8s [run_sortmerna.py] %(message)s')
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    # Write to file
    fileHandler = logging.FileHandler(log_fp)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    # Also write to STDOUT
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    # Get the reads
    try:
        reads_fp = get_file_from_url(args.input, temp_folder)
    except:
        exit_and_clean_up(temp_folder)

    # Get the database
    try:
        db_fp = get_file_from_url(args.db, temp_folder)
    except:
        exit_and_clean_up(temp_folder)

    # Run SortMeRNA

    aligned_fp = os.path.join(temp_folder, str(uuid.uuid4())[:4] + "-aligned")
    unaligned_fp = os.path.join(temp_folder, str(uuid.uuid4())[:4] + "-unaligned")
    logging.info("Running SortMeRNA")
    try:
        run_cmds([
            "sortmerna",
            "--ref", db_fp,
            "--reads", reads_fp,
            "--aligned", aligned_fp,
            "--other", unaligned_fp,
            "--fastx",
            "--log",
            "-a", str(args.threads),
            "-m", "4096"
        ])
    except:
        exit_and_clean_up(temp_folder)

    # Return the results, both the unaligned reads and the logs
    logging.info("Returning the unaligned reads and the logs")
    for local_path, remote_path in [
        (unaligned_fp + ".fastq", args.output_reads),
        (log_fp, args.output_logs)
    ]:
        # Make sure the local file exists
        try:
            assert os.path.exists(local_fp)
        except:
            exit_and_clean_up(temp_folder)

        # Upload results to S3, if specified
        if remote_path.startswith("s3://"):
            try:
                run_cmds([
                    "aws", "s3", "cp",
                    local_path,
                    remote_path
                ])
            except:
                exit_and_clean_up(temp_folder)
        else:
            try:
                run_cmds([
                    "cp",
                    local_path,
                    remote_path
                ])
            except:
                exit_and_clean_up(temp_folder)

    logging.info("Clean up all of the temporary files")
    shutil.rmtree(temp_folder)