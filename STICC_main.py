from STICC_solver import STICC
import numpy as np
import argparse

parser = argparse.ArgumentParser(description='Parameters of the STICC')
parser.add_argument('--fname', type=str,
                    default="synthetic_data.txt", help='Input data name')
parser.add_argument('--oname', type=str,
                    default="result_synthetic_data.txt", help='Output file name')
parser.add_argument('--attr_idx_start', type=int,
                    default=1, help='Attribute start index')
parser.add_argument('--attr_idx_end', type=int,
                    default=5, help='Attribute end index')
parser.add_argument('--spatial_idx_start', type=int,
                    default=6, help='Neighbouring object start index')
parser.add_argument('--spatial_idx_end', type=int, default=8,
                    help='Neighbouring object end index')
parser.add_argument('--spatial_radius', type=int,
                    default=3, help='Radius of the subregion')
parser.add_argument('--number_of_clusters', type=int,
                    default=5, help='Number of clusters')
parser.add_argument('--lambda_parameter', type=float,
                    default=0.1, help='Lambda')
parser.add_argument('--beta', type=float, default=5, help='Beta')
parser.add_argument('--maxIters', type=int, default=20, help='Max Iterations')

args = parser.parse_args()

sticc = STICC(spatial_radius=args.spatial_radius, number_of_clusters=args.number_of_clusters,
             lambda_parameter=args.lambda_parameter, beta=args.beta, maxIters=args.maxIters,
             threshold=2e-5, write_out_file=False, prefix_string="output_folder/", num_proc=1,
             attr_idx_start=args.attr_idx_start, attr_idx_end=args.attr_idx_end,
             spatial_idx_start=args.spatial_idx_start, spatial_idx_end=args.spatial_idx_end)
(cluster_assignment, cluster_MRFs) = sticc.fit(input_file=args.fname)

# Save cluster output
print(cluster_assignment)
np.savetxt(args.oname, cluster_assignment, fmt='%d', delimiter=',')

# Save MRF as npy
for key, value in cluster_MRFs.items():
    with open(f'output_folder/MRF_{args.fname.split(".")[0]}_{key}.npy', 'wb') as f:
        np.save(f, np.array(value))
