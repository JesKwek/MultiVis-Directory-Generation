# SPRITEVisu Directory Generation

**SPRITEVisu** is a tool for generating heatmap visualizations of genomic contacts from SPRITE (Split-Pool Recognition of Interactions by Tag Extension) data.
It require a specific directory format which **SPRITEVisu Directory Generation** is designed to process cluster files, handle intra- and interchromosomal contacts, 
and create output files compatible with genomic visualization tools (SPRITEVisu).

Portions of this code are adapted from the Guttman Lab's SPRITE pipeline, available at: [Guttman Lab SPRITE Pipeline](https://github.com/GuttmanLab/sprite-pipeline/blob/master/scripts/python/contact.py).

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Example](#example)
- [Credits](#credits)

## Installation

### Prerequisites

- Python 3.7 or higher
- Required Python libraries: `numpy`, `collections`, `json`, `os`

To install the required libraries, run:

### Clone the Repository
To clone the repository, run:

```
git clone https://github.com/JesKwek/SPRITEVisu-Directory-Generation
cd SPRITEVisu-Directory-Generation
```

## Usage
To run SpriteVisu, use the main_sv.py script:

```
python main_sv.py -c <clusters_file> -s <genomic_size_file> -o <output_directory> -m <max_cluster_size> -n <min_cluster_size> [-t]
```

**Arguments**
- `-c`, `--clusters`: Path to the input clusters file (required).
- `-s`, `--genomic_size`: Path to the JSON file containing genomic size information, e.g., chromsize_hg38.json (Sample can be found at ).
- `-o`, `--heatmap_spritevisu_output`: Output directory for the generated SpriteVisu heatmap file (default: spritevisu).
- `-m`, `--max_cluster_size`: Maximum number of reads allowed in a read-cluster. Clusters with more reads than this value will be skipped (default: 1000).
- `-n`, `--min_cluster_size`: Minimum number of reads required in a read-cluster. Clusters with fewer reads than this value will be skipped (default: 2).
- `-t`, `--start_only`: Flag to indicate whether the cluster file contains only start positions. If this flag is set, the script assumes that the cluster file has start positions only (default: False).

## Example
```
python main_sv.py -c ./data/human.combined.mapq-ge10.clusters -s chromsize_hg19.json  -o SPRITEVisu_human.combined.mapq-ge10 -m 100 -n 2 -t
```
This example uses human.combined.mapq-ge10.clusters produced by Guttman et al and can be download at [GSE114242_human_combined_clusters.tar.gz](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE114242). It uses the genomic size file [chromsize_hg38.json](./chromsize_hg19.json), and outputs to the output_directory. In this case, `./SPRITEVisu_human.combined.mapq-ge10 `. It also sets the maximum cluster size to 100, the minimum cluster size to 2, and uses only the start positions because this cluster file only contains the start position. For newer SPRITE data, you should set this -t as it will have both start and end position.

## Credits
This tool was developed by Jes Kwek Hui Min. Portions of the code were derived or adapted from the Guttman Lab's SPRITE pipeline, which is available here.
