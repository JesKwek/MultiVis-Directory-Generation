# Data to SPRITE Cluster Format Converter

This guide outlines a **generic workflow** for converting genomic data into **SPRITE (Split-Pool Recognition of Interactions by Tag Extension)** cluster format. You can adapt these steps to your preferred clustering algorithm or any other method for generating clusters. The essential requirement is that each **cluster** has a unique **barcode** and a set of **genomic positions** in **SPRITE format**.

The final output will always follow this structure:

```
barcode    read_1    read_2    read_3    ...
```

Where:
- `barcode`: Unique identifier for each cluster
- `read_1, read_2, etc.`: Genomic positions associated with the cluster

Once you get the cluster file, you can convert into the MultiVis directory format and use our tools.

## General Concept

The converter takes your data and:
1. Groups data points based on rules specific to your dataset (e.g., distance, similarity, etc.)  
2. Creates **unique identifiers (barcodes)** for each cluster  
3. Associates **genomic positions** with each cluster  
4. Outputs the data in **SPRITE cluster format**  

Below is a **working code example** for a MERFISH dataset (`genomic-scale.tsv`) that demonstrates how you might implement this conversion. Note that this script is meant as a **guide**, not as a guaranteed, fully validated method.

## Example: MERFISH to SPRITE Code

```python
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import pdist, squareform

def calculate_spatial_distances(points):
    """Calculate pairwise distances between points in 3D space."""
    return squareform(pdist(points))

def cluster_by_distance(df, eps=1000, min_samples=2):
    """
    Cluster points based on spatial proximity.
    eps: maximum distance between points in a cluster (in nm).
    min_samples: minimum number of points to form a cluster.
    """
    # Extract spatial coordinates (x, y, z)
    coords = df[['x(nm)', 'y(nm)', 'z(nm)']].values
    
    # Remove rows with NaN coordinates
    valid_mask = ~np.isnan(coords).any(axis=1)
    coords = coords[valid_mask]
    
    # Perform DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean').fit(coords)
    
    return clustering.labels_, valid_mask

def convert_merfish_to_sprite(input_file, output_file, eps=1000, min_samples=2):
    # 1. Read the MERFISH data
    print("Reading MERFISH data...")
    df = pd.read_csv(input_file, sep='\t')
    
    # Clean column names (remove whitespace)
    df.columns = df.columns.str.strip()
    
    # 2. Create a base barcode from cell number and experiment number
    df['base_barcode'] = 'cell_' + df['cell number'].astype(str) + '_exp_' + df['experiment number'].astype(str)
    
    # 3. Extract chromosome and position from the 'genomic coordinate'
    def parse_genomic_coord(coord):
        if pd.isna(coord):
            return None
        try:
            chrom, pos = coord.split(':')
            start, end = pos.split('-')
            # Use the midpoint of the range as the representative position
            mid_point = (int(start) + int(end)) // 2
            return f"{chrom}:{mid_point}"
        except:
            return None
    
    # Create a 'read' column containing a simplified genomic position
    df['read'] = df['genomic coordinate'].apply(parse_genomic_coord)
    
    # Remove rows that do not have a valid 'read'
    df = df.dropna(subset=['read'])
    
    # 4. Perform spatial clustering
    print("Performing spatial clustering...")
    cluster_labels, valid_mask = cluster_by_distance(df, eps=eps, min_samples=min_samples)
    
    # Only assign cluster labels to valid rows
    df.loc[valid_mask, 'cluster'] = cluster_labels
    
    # 5. Combine the base barcode with the cluster label
    df['barcode'] = df['base_barcode'] + '_cluster_' + df['cluster'].astype(str)
    
    # 6. Group by barcode to create the final SPRITE clusters
    clusters = df.groupby('barcode')['read'].agg(list).reset_index()
    
    # 7. Write the data to the output file in SPRITE format
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
    # min_samples=2 means at least 2 points are required to form a cluster
    convert_merfish_to_sprite(input_file, output_file, eps=1000, min_samples=2)
```


## How the Codes works

1. Reading and Preprocessing
- The script reads a TSV file (input_file) into a pandas DataFrame (df).
- It cleans up column headers by stripping whitespace.

2. Creating a Base Barcode
- Each row gets a base_barcode using the columns cell number and experiment number, formatted as cell_X_exp_Y.

3. Parsing Genomic Coordinates
- The function parse_genomic_coord() takes a string like "chr1:2950000-3050000" and returns "chr1:3000000" (using the midpoint).
- This step ensures the genomic coordinate is in a simplified, single-position format.

4. Spatial Clustering
- The function cluster_by_distance() performs DBSCAN clustering.
- Any rows with NaN (missing) coordinates are excluded from clustering.

5. Assigning Cluster Labels
- Once DBSCAN finishes, each valid data point is assigned a cluster label (0, 1, 2, …, or -1 for outliers).
- Each cluster label is appended to the base_barcode to form the final barcode (e.g., cell_1_exp_1_cluster_0).

6. Grouping Reads by Barcode
- The script groups all rows by their barcode and aggregates the read entries into a list.

7. Writing SPRITE Output
- Each cluster becomes a line in the output file.
- The first column is the barcode, followed by each read in that cluster (separated by tabs).

### Example output format

```
cell_1_exp_1_cluster_0    chr1:3000000    chr1:6000000    chr1:12000000
cell_1_exp_1_cluster_1    chr2:1500000    chr2:3000000
cell_2_exp_1_cluster_0    chr1:2500000    chr1:4500000
```

# Note
This method had be been verified. You should always verify that your clusters make sense for your specific experimental or analytical goals.