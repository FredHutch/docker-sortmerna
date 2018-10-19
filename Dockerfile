FROM ubuntu:16.04
MAINTAINER sminot@fredhutch.org

# Install prerequisites
RUN apt update && \
	apt-get install -y build-essential wget unzip python3 \
					   python3-dev git python3-pip bats awscli \
					   libcurl4-openssl-dev zlib1g-dev curl 

RUN pip3 install numpy==1.15.2 && \
	pip3 install scikit-bio==0.5.4

# Use /share as the working directory
RUN mkdir /share
WORKDIR /share

# Add /scratch
RUN mkdir /scratch

# Folder for installation
RUN mkdir /usr/sortmerna

# Download the precompiled linux binary
RUN cd /usr/sortmerna/ && \
	wget https://github.com/biocore/sortmerna/releases/download/2.1b/sortmerna-2.1b-linux.tar.gz && \
	tar xzvf sortmerna-2.1b-linux.tar.gz && \
	chmod +x /usr/sortmerna/sortmerna-2.1b/sortmerna && \
	chmod +x /usr/sortmerna/sortmerna-2.1b/indexdb_rna && \
	ln -s /usr/sortmerna/sortmerna-2.1b/sortmerna /usr/local/bin/ && \
	ln -s /usr/sortmerna/sortmerna-2.1b/indexdb_rna /usr/local/bin/

# Add the local directory to the container
ADD . /usr/sortmerna
# Add the run script to the PATH
RUN ln -s /usr/sortmerna/run_sortmerna.py /usr/local/bin/

# Run tests and then remove the folder
RUN bats /usr/sortmerna/tests/ && rm -r /usr/sortmerna/tests/
