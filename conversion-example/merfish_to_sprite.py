import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import pdist, squareform

def calculate_spatial_distances(points):
    """Calculate pairwise distances between points in 3D space"""
    return squareform(pdist(points))

def cluster_by_distance(df, eps=1000, min_samples=2):
    """
    Cluster points based on spatial proximity
    eps: maximum distance between points in a cluster (in nm)
    min_samples: minimum number of points to form a cluster
    """
    # Extract spatial coordinates
    coords = df[['x(nm)', 'y(nm)', 'z(nm)']].values
    
    # Remove rows with NaN coordinates
    valid_mask = ~np.isnan(coords).any(axis=1)
    coords = coords[valid_mask]
    
    # Perform DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean').fit(coords)
    
    return clustering.labels_, valid_mask

def convert_merfish_to_sprite(input_file, output_file, eps=1000, min_samples=2):
    # Read the MERFISH data
    print("Reading MERFISH data...")
    df = pd.read_csv(input_file, sep='\t')
    
    # Clean column names (remove any whitespace)
    df.columns = df.columns.str.strip()
    
    # Create base barcode from cell number and experiment number
    df['base_barcode'] = 'cell_' + df['cell number'].astype(str) + '_exp_' + df['experiment number'].astype(str)
    
    # Extract chromosome and position from genomic coordinate
    def parse_genomic_coord(coord):
        if pd.isna(coord):
            return None
        try:
            chrom, pos = coord.split(':')
            start, end = pos.split('-')
            # Use middle point of the range as position
            mid_point = (int(start) + int(end)) // 2
            return f"{chrom}:{mid_point}"
        except:
            return None
    
    # Create read column from genomic coordinates
    df['read'] = df['genomic coordinate'].apply(parse_genomic_coord)
    
    # Remove rows with NaN reads
    df = df.dropna(subset=['read'])
    
    # Perform spatial clustering
    print("Performing spatial clustering...")
    cluster_labels, valid_mask = cluster_by_distance(df, eps=eps, min_samples=min_samples)
    
    # Add cluster labels to the dataframe
    df.loc[valid_mask, 'cluster'] = cluster_labels
    
    # Create final barcode combining base barcode and spatial cluster
    df['barcode'] = df['base_barcode'] + '_cluster_' + df['cluster'].astype(str)
    
    # Group by barcode to create SPRITE clusters
    clusters = df.groupby('barcode')['read'].agg(list).reset_index()
    
    # Write to output file in SPRITE format
    print("Writing SPRITE cluster format...")
    with open(output_file, 'w') as f:
        for _, row in clusters.iterrows():
            barcode = row['barcode']
            reads = row['read']
            f.write(f"{barcode}\t" + "\t".join(reads) + "\n")
    
    print(f"Conversion complete. Output written to {output_file}")
    print(f"Total number of clusters: {len(clusters)}")

if __name__ == "__main__":
    input_file = "genomic-scale.tsv"
    output_file = "sprite_clusters.txt"
    # eps=1000 means points within 1000nm will be considered in the same cluster
    # min_samples=2 means at least 2 points are needed to form a cluster
    convert_merfish_to_sprite(input_file, output_file, eps=1000, min_samples=2) 