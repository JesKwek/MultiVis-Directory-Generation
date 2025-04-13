import json
import os
import collections
from itertools import combinations
import sqlite3

__author__ = "Jes Kwek Hui Min"
# Portions of this code, particularly for reading SPRITE cluster files,
# handling intra- and interchromosomal contacts, and writing contact data
# to output files, are derived or adapted from the Guttman Lab's SPRITE pipeline:
# https://github.com/GuttmanLab/sprite-pipeline/blob/master/scripts/python/contact.py

class SpriteVisu:
    """
    A class to handle the generation of SpriteVisu files for visualizing genomic contacts.

    This class reads cluster files, processes intra- and interchromosomal contacts,
    and generates heatmap files for use in genomic visualization tools. Portions of the
    code are adapted from the Guttman Lab's SPRITE pipeline.

    Attributes:
        _cluster_file (str): Path to the cluster file.
        _max_cluster_size (int): Maximum number of reads allowed in a read-cluster.
        _min_cluster_size (int): Minimum number of reads required in a read-cluster.
        _contact_lists (defaultdict): Stores contacts for each chromosome pair.
        _start_only (bool): Specifies if the input cluster file contains only start positions.
        _genomic_sizes (dict): Stores genomic size information loaded from a JSON file.
        _chromosome_list (list): List of chromosomes parsed from the genomic size information.
    """

    def __init__(self, cluster_file, genomic_size_file, max_cluster, min_cluster, start_only):
        """
        Initializes the SpriteVisu class with necessary parameters.

        Args:
            cluster_file (str): Path to the input clusters file.
            genomic_size_file (str): Path to the JSON file containing genomic size information.
            max_cluster (int): Maximum number of reads allowed in a read-cluster.
            min_cluster (int): Minimum number of reads required in a read-cluster.
            start_only (bool): Indicates if the input cluster file contains only start positions.
        """
        self._cluster_file = cluster_file
        self._max_cluster_size = max_cluster
        self._min_cluster_size = min_cluster
        self._contact_lists = collections.defaultdict(list)
        self._start_only = start_only

        with open(genomic_size_file, 'r') as file:
            self._genomic_sizes = json.load(file)
            self._chromosome_list = self._genomic_sizes["chromosomes"].keys()

    def save_meta(self, directory):
        """
        Saves genomic size information to a meta.json file in the specified directory.

        Args:
            directory (str): The directory where the meta.json file will be saved.
        """
        with open(os.path.join(directory, 'meta.json'), 'w') as json_file:
            json.dump(self._genomic_sizes, json_file)

    def add_contact_to_list(self, cluster_id, chrom1, start1, chrom2, start2, inc1, inc2):
        """
        Adds a contact to the contact list.

        Args:
            chrom1 (str): First chromosome involved in the contact.
            start1 (int): Start position on the first chromosome.
            chrom2 (str): Second chromosome involved in the contact.
            start2 (int): Start position on the second chromosome.
            inc1 (int): Increment value for the first chromosome's contacts. total_inc (NOT_USED).
            inc2 (int): Increment value for the second chromosome's contacts. specific_inc.
        """
        if chrom1 not in self._chromosome_list or chrom2 not in self._chromosome_list:
            return

        # Ensure consistent ordering of chromosome pairs
        if chrom1 > chrom2:
            chrom1, chrom2 = chrom2, chrom1
            start1, start2 = start2, start1

        contact_key = f"{chrom1}-{chrom2}"
        self._contact_lists[contact_key].append(f"{start1},{start2},{inc2}")
        #self._contact_lists[contact_key].append(f"{start1},{start2},{inc1},{inc2}")

    def generate_hsv(self, output):
        """
        Generates the SpriteVisu heatmap file based on cluster data.

        Args:
            output (str): Output directory where the generated files will be saved.
        """
        os.makedirs(output, exist_ok=True)
        self.save_meta(output)
        if self._start_only:
            file_path = os.path.join(output, f"cluster_id_reads-startonly.db")
            conn = sqlite3.connect(file_path)
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    chromosome TEXT,
                    start INTEGER,
                    cluster_id TEXT
               )
           ''')
        else:
            file_path = os.path.join(output, f"cluster_id_reads.db")
            conn = sqlite3.connect(file_path)
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    chromosome TEXT,
                    start INTEGER,
                    end INTEGER,
                    cluster_id TEXT
               )
           ''')

        with open(self._cluster_file, 'r') as file:
            for line in file:
                data_split = line.split()
                reads = data_split[1:]
                cluster_id = data_split[0]
                reads_len = len(reads)
                if not self._min_cluster_size <= reads_len <= self._max_cluster_size:
                    print(reads_len)
                    continue

                bins = collections.defaultdict(set)

                for read in reads:
                    # For the current SPRITE pipeline
                    if not self._start_only:
                        _, coord = read.rsplit('_', 1)
                        chrom, position = coord.split(':')
                        start, end = position.split('-')
                        bins[chrom].add(int(start))
                        cur.execute("INSERT INTO contacts VALUES (?, ?, ?, ?)", (chrom, start, end, cluster_id))
                    else:
                        # Legacy format handling
                        chrom, start = read.split(':', 1)
                        bins[chrom].add(int(start))
                        cur.execute("INSERT INTO contacts VALUES (?, ?, ?)", (chrom, start, cluster_id))


                # Process intrachromosomal contacts
                for chrom, bin_set in bins.items():
                    inc1 = len(bin_set)
                    if inc1 > 1:
                        for start1, start2 in combinations(bin_set, 2):
                            inc2 = len(bin_set)  # For intrachromosomal contacts, inc2 is the length of the bin set
                            self.add_contact_to_list(cluster_id, chrom, start1, chrom, start2, reads_len, inc2)

                # Process interchromosomal contacts
                if len(bins) > 1:
                    chrom_list = list(bins.keys())
                    for i in range(len(chrom_list)):
                        for j in range(i + 1, len(chrom_list)):
                            chrom1 = chrom_list[i]
                            chrom2 = chrom_list[j]
                            bin_set1 = bins[chrom1]
                            bin_set2 = bins[chrom2]
                            inc1 = len(bin_set1) + len(bin_set2)
                            inc2 = inc1  # For interchromosomal contacts, inc2 is the sum of lengths of both bin sets
                            for start1 in bin_set1:
                                for start2 in bin_set2:
                                    self.add_contact_to_list(cluster_id, chrom1, start1, chrom2, start2, reads_len, inc2)

        self.write_contact_files(output)
        conn.commit()
        conn.close()

    def write_contact_files(self, output_dir):
        """
        Writes the contacts to files in the specified output directory.

        Args:
            output_dir (str): The directory where the contact files will be saved.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for contact_key, contacts in self._contact_lists.items():
            file_path = os.path.join(output_dir, f"{contact_key}.txt")
            with open(file_path, 'w') as f:
                f.write("\n".join(contacts))
