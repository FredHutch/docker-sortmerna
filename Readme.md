# Docker image for SortMeRNA



```run_sortmerna.py -h

usage: run_sortmerna.py [-h] --input INPUT --output-reads OUTPUT_READS
                        --output-logs OUTPUT_LOGS [--db DB]
                        [--threads THREADS] [--temp-folder TEMP_FOLDER]

Filter a set of reads with SortMeRNA.

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT         Location for input file. (Supported: local path,
                        s3://, or ftp://).
  --output-reads OUTPUT_READS
                        Path for output reads.
  --output-logs OUTPUT_LOGS
                        Path for output logs.
  --db DB               Path for database.
  --threads THREADS     Number of threads to use for alignment.
  --temp-folder TEMP_FOLDER
                        Folder used for temporary files.
```
