import argparse
from HeatmapMultiVisu import SpriteVisu

__author__ = "Jes Kwek Hui Min"
# Usage: python script_name.py -c <clusters_file> -s <genomic_size_file> -o <output_file> -m 100 -n 2 -t

def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Extract argument values
    cluster_filepath = args.clusters
    genomic_size_filepath = args.genomic_size
    output_filepath = args.heatmap_spritevisu_output
    max_cluster_size = args.max_cluster_size
    min_cluster_size = args.min_cluster_size
    start_only = args.start_only

    # Initialize the SpriteVisu object with the provided arguments
    sprite_visu = SpriteVisu(cluster_filepath, genomic_size_filepath, max_cluster_size, min_cluster_size, start_only)

    # Generate the heatmap visualization
    sprite_visu.generate_hsv(output_filepath)


def parse_arguments():
    """
    Parses command-line arguments for the script.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='Generate a SpriteVisu file for use in SpriteVisu interactive tools.')

    parser.add_argument('-c', '--clusters',
                        metavar="FILE",
                        action="store",
                        required=True,
                        help="Path to the input clusters file.")

    parser.add_argument('-s', '--genomic_size',
                        metavar="FILE",
                        action="store",
                        required=True,
                        help="Path to the JSON file containing genomic size information, e.g., chromsize_hg19.json.")

    parser.add_argument('-o', '--heatmap_spritevisu_output',
                        metavar="FILE",
                        action="store",
                        default="spritevisu",
                        help="Output directory for the generated SpriteVisu heatmap file. (default: 'spritevisu')")

    parser.add_argument('-m', '--max_cluster_size',
                        metavar='MAX',
                        type=int,
                        action='store',
                        default=1000,
                        help="Maximum number of reads allowed in a read-cluster. "
                             "Clusters with more reads than this value will be skipped. (default: 1000)")

    parser.add_argument('-n', '--min_cluster_size',
                        metavar='MIN',
                        type=int,
                        action='store',
                        default=2,
                        help="Minimum number of reads required in a read-cluster. "
                             "Clusters with fewer reads than this value will be skipped. (default: 2)")

    parser.add_argument('-t', '--start_only',
                        action='store_true',
                        help="Indicate whether the cluster file contains only start positions. "
                             "If this flag is set, the script assumes that the cluster file has start positions only. (default: False)")

    return parser.parse_args()


if __name__ == "__main__":
    main()
