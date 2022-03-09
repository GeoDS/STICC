from src.admm_solver import ADMMSolver
from src.STICC_helper import *
from multiprocessing import Pool
import pandas as pd
from sklearn.cluster import KMeans
from sklearn import mixture
import matplotlib.pyplot as plt
import numpy as np
import math
import time
import collections
import os
import errno
import sys
import code
import random
import matplotlib
matplotlib.use('Agg')


class STICC:
    def __init__(self, spatial_radius=1, number_of_clusters=5, lambda_parameter=11e-2,
                 beta=400, maxIters=1000, threshold=2e-5, write_out_file=False,
                 prefix_string="", num_proc=1, cluster_reassignment=20, biased=False,
                 attr_idx_start=0, attr_idx_end=0, spatial_idx_start=0, spatial_idx_end=0):
        """
        Parameters:
            - spatial_radius: size of the subregion
            - number_of_clusters: number of clusters
            - lambda_parameter: sparsity parameter
            - switch_penalty: temporal consistency parameter
            - maxIters: number of iterations
            - threshold: convergence threshold
            - write_out_file: (bool) if true, prefix_string is output file dir
            - prefix_string: output directory if necessary
            - cluster_reassignment: number of points to reassign to a 0 cluster
            - biased: Using the biased or the unbiased covariance
        """
        self.spatial_radius = spatial_radius
        self.number_of_clusters = number_of_clusters
        self.lambda_parameter = lambda_parameter
        self.switch_penalty = beta
        self.maxIters = maxIters
        self.threshold = threshold
        self.write_out_file = write_out_file
        self.prefix_string = prefix_string
        self.num_proc = num_proc
        self.cluster_reassignment = cluster_reassignment
        self.num_blocks = self.spatial_radius + 1
        self.biased = biased
        self.attr_idx_start = attr_idx_start
        self.attr_idx_end = attr_idx_end
        self.spatial_idx_start = spatial_idx_start
        self.spatial_idx_end = spatial_idx_end
        self.spatial_series_index = []
        self.spatial_series_close = []
        self.spatial_series_closest = []
        pd.set_option('display.max_columns', 500)
        np.set_printoptions(
            formatter={'float': lambda x: "{0:0.4f}".format(x)})
        np.random.seed(102)

    def fit(self, input_file):
        """
        Main method for TICC solver.
        Parameters:
            - input_file: location of the data file
        """
        assert self.maxIters > 0  # must have at least one iteration
        self.log_parameters()

        # Get data into proper format

        total_arr, total_rows_size, total_cols_size = self.load_data(
            input_file)
        spatial_series_arr = total_arr[:,
                                       self.attr_idx_start:self.attr_idx_end+1]
        spatial_series_rows_size = total_rows_size
        spatial_series_col_size = self.attr_idx_end - self.attr_idx_start + 1
        spatial_series_index = total_arr[:, 0]
        spatial_series_close = total_arr[:,
                                         self.spatial_idx_start:self.spatial_idx_end+1]
        print(spatial_series_col_size, spatial_series_arr.shape,
              spatial_series_close.shape)
        self.spatial_series_closest = spatial_series_close[:, 0]
        self.spatial_series_index = spatial_series_index
        self.spatial_series_close = spatial_series_close

        ############
        # The basic folder to be created
        str_NULL = self.prepare_out_directory()

        # Train test split
        training_indices = spatial_series_index
        num_train_points = len(training_indices)

        # Stack the training data
        complete_D_train = self.stack_training_data(total_arr, spatial_series_col_size, num_train_points,
                                                    training_indices, spatial_series_col_size)

        # Initialization
        # Gaussian Mixture
        gmm = mixture.GaussianMixture(
            n_components=self.number_of_clusters, covariance_type="full")
        gmm.fit(complete_D_train)
        clustered_points = gmm.predict(complete_D_train)
        gmm_clustered_pts = clustered_points + 0
        # K-means
        kmeans = KMeans(n_clusters=self.number_of_clusters,
                        n_init=300, random_state=0).fit(complete_D_train)
        clustered_points = kmeans.labels_
        # todo, is there a difference between these two?
        clustered_points_kmeans = kmeans.labels_
        kmeans_clustered_pts = kmeans.labels_

        train_cluster_inverse = {}
        log_det_values = {}  # log dets of the thetas
        computed_covariance = {}
        cluster_mean_info = {}
        cluster_mean_stacked_info = {}
        old_clustered_points = None  # points from last iteration

        empirical_covariances = {}

        # PERFORM TRAINING ITERATIONS
        pool = Pool(processes=self.num_proc)  # multi-threading
        for iters in range(self.maxIters):
            print("\n\n\nITERATION ###", iters)
            # Get the train and test points
            train_clusters_arr = collections.defaultdict(
                list)  # {cluster: [point indices]}
            for point, cluster_num in enumerate(clustered_points):
                train_clusters_arr[cluster_num].append(point)

            len_train_clusters = {
                k: len(train_clusters_arr[k]) for k in range(self.number_of_clusters)}

            # train_clusters holds the indices in complete_D_train
            # for each of the clusters
            opt_res = self.train_clusters(cluster_mean_info, cluster_mean_stacked_info, complete_D_train,
                                          empirical_covariances, len_train_clusters, spatial_series_col_size, pool,
                                          train_clusters_arr)

            self.optimize_clusters(computed_covariance, len_train_clusters, log_det_values, opt_res,
                                   train_cluster_inverse)

            # update old computed covariance
            old_computed_covariance = computed_covariance

            print("UPDATED THE OLD COVARIANCE")

            self.trained_model = {'cluster_mean_info': cluster_mean_info,
                                  'computed_covariance': computed_covariance,
                                  'cluster_mean_stacked_info': cluster_mean_stacked_info,
                                  'complete_D_train': complete_D_train,
                                  'spatial_series_col_size': spatial_series_col_size}
            clustered_points = self.predict_clusters()

            # recalculate lengths
            new_train_clusters = collections.defaultdict(
                list)  # {cluster: [point indices]}
            for point, cluster in enumerate(clustered_points):
                new_train_clusters[cluster].append(point)

            len_new_train_clusters = {
                k: len(new_train_clusters[k]) for k in range(self.number_of_clusters)}

            before_empty_cluster_assign = clustered_points.copy()

            if iters != 0:
                cluster_norms = [(np.linalg.norm(old_computed_covariance[self.number_of_clusters, i]), i) for i in
                                 range(self.number_of_clusters)]
                norms_sorted = sorted(cluster_norms, reverse=True)
                # clusters that are not 0 as sorted by norm
                valid_clusters = [
                    cp[1] for cp in norms_sorted if len_new_train_clusters[cp[1]] != 0]

                # Add a point to the empty clusters
                # assuming more non empty clusters than empty ones
                counter = 0
                for cluster_num in range(self.number_of_clusters):
                    if len_new_train_clusters[cluster_num] == 0:
                        # a cluster that is not len 0
                        cluster_selected = valid_clusters[counter]
                        counter = (counter + 1) % len(valid_clusters)
                        print("cluster that is zero is:", cluster_num,
                              "selected cluster instead is:", cluster_selected)
                        start_point = np.random.choice(
                            new_train_clusters[cluster_selected])  # random point number from that cluster
                        for i in range(0, self.cluster_reassignment):
                            # put cluster_reassignment points from point_num in this cluster
                            point_to_move = start_point + i
                            if point_to_move >= len(clustered_points):
                                break
                            clustered_points[point_to_move] = cluster_num
                            computed_covariance[self.number_of_clusters, cluster_num] = old_computed_covariance[
                                self.number_of_clusters, cluster_selected]
                            cluster_mean_stacked_info[self.number_of_clusters, cluster_num] = complete_D_train[
                                point_to_move, :]
                            cluster_mean_info[self.number_of_clusters, cluster_num] \
                                = complete_D_train[point_to_move, :][
                                (self.spatial_radius - 1) * spatial_series_col_size:self.spatial_radius * spatial_series_col_size]

            for cluster_num in range(self.number_of_clusters):
                print("length of cluster #", cluster_num, "-------->",
                      sum([x == cluster_num for x in clustered_points]))

            # TEST SETS STUFF
            # LLE + swtiching_penalty
            # Segment length
            # Get the train and test points
            train_confusion_matrix_EM = compute_confusion_matrix(self.number_of_clusters, clustered_points,
                                                                 training_indices)
            train_confusion_matrix_GMM = compute_confusion_matrix(self.number_of_clusters, gmm_clustered_pts,
                                                                  training_indices)
            train_confusion_matrix_kmeans = compute_confusion_matrix(self.number_of_clusters, kmeans_clustered_pts,
                                                                     training_indices)
            # compute the matchings
            matching_EM, matching_GMM, matching_Kmeans = self.compute_matches(train_confusion_matrix_EM,
                                                                              train_confusion_matrix_GMM,
                                                                              train_confusion_matrix_kmeans)

            print("\n\n\n")

            if np.array_equal(old_clustered_points, clustered_points):
                print("\n\n\n\nCONVERGED!!! BREAKING EARLY!!!")
                break
            old_clustered_points = before_empty_cluster_assign
            # end of training
        if pool is not None:
            pool.close()
            pool.join()
        train_confusion_matrix_EM = compute_confusion_matrix(self.number_of_clusters, clustered_points,
                                                             training_indices)
        train_confusion_matrix_GMM = compute_confusion_matrix(self.number_of_clusters, gmm_clustered_pts,
                                                              training_indices)
        train_confusion_matrix_kmeans = compute_confusion_matrix(self.number_of_clusters, clustered_points_kmeans,
                                                                 training_indices)

        return clustered_points, train_cluster_inverse

    def compute_matches(self, train_confusion_matrix_EM, train_confusion_matrix_GMM, train_confusion_matrix_kmeans):
        matching_Kmeans = find_matching(train_confusion_matrix_kmeans)
        matching_GMM = find_matching(train_confusion_matrix_GMM)
        matching_EM = find_matching(train_confusion_matrix_EM)
        correct_e_m = 0
        correct_g_m_m = 0
        correct_k_means = 0
        for cluster in range(self.number_of_clusters):
            matched_cluster_e_m = matching_EM[cluster]
            matched_cluster_g_m_m = matching_GMM[cluster]
            matched_cluster_k_means = matching_Kmeans[cluster]

            correct_e_m += train_confusion_matrix_EM[cluster,
                                                     matched_cluster_e_m]
            correct_g_m_m += train_confusion_matrix_GMM[cluster,
                                                        matched_cluster_g_m_m]
            correct_k_means += train_confusion_matrix_kmeans[cluster,
                                                             matched_cluster_k_means]
        return matching_EM, matching_GMM, matching_Kmeans

    def smoothen_clusters(self, cluster_mean_info, computed_covariance,
                          cluster_mean_stacked_info, complete_D_train, n):
        clustered_points_len = len(complete_D_train)
        inv_cov_dict = {}  # cluster to inv_cov
        log_det_dict = {}  # cluster to log_det
        for cluster in range(self.number_of_clusters):
            cov_matrix = computed_covariance[self.number_of_clusters, cluster][0:(2 * (self.num_blocks - 1)-1) * n,
                                                                               0:(2 * (self.num_blocks - 1)-1) * n]
            inv_cov_matrix = np.linalg.inv(cov_matrix)
            log_det_cov = np.log(np.linalg.det(cov_matrix)
                                 )  # log(det(sigma2|1))
            inv_cov_dict[cluster] = inv_cov_matrix
            log_det_dict[cluster] = log_det_cov
        # For each point compute the LLE
        print("beginning the smoothening ALGORITHM")
        LLE_all_points_clusters = np.zeros(
            [clustered_points_len, self.number_of_clusters])
        for point in range(clustered_points_len):
            if point + self.spatial_radius - 1 < complete_D_train.shape[0]:
                for cluster in range(self.number_of_clusters):
                    cluster_mean = cluster_mean_info[self.number_of_clusters, cluster]
                    cluster_mean_stacked = cluster_mean_stacked_info[self.number_of_clusters, cluster]
                    x = complete_D_train[point, :] - \
                        cluster_mean_stacked[0:(
                            2 * (self.num_blocks - 1)-1) * n]
                    inv_cov_matrix = inv_cov_dict[cluster]
                    log_det_cov = log_det_dict[cluster]
                    lle = np.dot(x.reshape([1, (self.spatial_radius) * n]),
                                 np.dot(inv_cov_matrix, x.reshape([n * (self.spatial_radius), 1]))) + log_det_cov
                    LLE_all_points_clusters[point, cluster] = lle

        return LLE_all_points_clusters

    def optimize_clusters(self, computed_covariance, len_train_clusters, log_det_values, optRes, train_cluster_inverse):
        for cluster in range(self.number_of_clusters):
            if optRes[cluster] == None:
                continue
            val = optRes[cluster].get()
            print("OPTIMIZATION for Cluster #", cluster, "DONE!!!")
            # THIS IS THE SOLUTION
            S_est = upperToFull(val, 0)
            X2 = S_est
            u, _ = np.linalg.eig(S_est)
            cov_out = np.linalg.inv(X2)

            # Store the log-det, covariance, inverse-covariance, cluster means, stacked means
            log_det_values[self.number_of_clusters,
                           cluster] = np.log(np.linalg.det(cov_out))
            computed_covariance[self.number_of_clusters, cluster] = cov_out
            train_cluster_inverse[cluster] = X2
        for cluster in range(self.number_of_clusters):
            print("length of the cluster ", cluster,
                  "------>", len_train_clusters[cluster])

    def train_clusters(self, cluster_mean_info, cluster_mean_stacked_info, complete_D_train, empirical_covariances,
                       len_train_clusters, n, pool, train_clusters_arr):
        optRes = [None for i in range(self.number_of_clusters)]
        for cluster in range(self.number_of_clusters):
            cluster_length = len_train_clusters[cluster]
            if cluster_length != 0:
                size_blocks = n
                indices = train_clusters_arr[cluster]
                D_train = np.zeros([cluster_length, (self.spatial_radius) * n])
                for i in range(cluster_length):
                    point = indices[i]
                    D_train[i, :] = complete_D_train[point, :]

                cluster_mean_info[self.number_of_clusters, cluster] = np.mean(D_train, axis=0)[
                    (
                        self.spatial_radius - 1) * n:self.spatial_radius * n].reshape(
                    [1, n])
                cluster_mean_stacked_info[self.number_of_clusters, cluster] = np.mean(
                    D_train, axis=0)
                # Fit a model - OPTIMIZATION
                probSize = (self.spatial_radius) * size_blocks
                lamb = np.zeros((probSize, probSize)) + self.lambda_parameter
                S = np.cov(np.transpose(D_train), bias=self.biased)
                empirical_covariances[cluster] = S

                rho = 1
                solver = ADMMSolver(
                    lamb, (self.spatial_radius), size_blocks, 1, S)
                # apply to process pool
                optRes[cluster] = pool.apply_async(
                    solver, (1000, 1e-6, 1e-6, False,))
        return optRes

    def stack_training_data(self, Data, n, num_train_points, training_indices, spatial_cols_size):
        complete_D_train = np.zeros(
            [num_train_points, self.spatial_radius * n])
        # STICC data stack
        for i in range(num_train_points):
            for k in range(self.spatial_radius):
                if k == 0:
                    complete_D_train[i][k * n:(k + 1) * n] = Data[i][1:(n + 1)]
                else:
                    complete_D_train[i][k * n:(k + 1) *
                                        n] = Data[int(Data[i][n + k])][1:(n + 1)]
        return complete_D_train

    def prepare_out_directory(self):
        str_NULL = self.prefix_string
        if not os.path.exists(os.path.dirname(str_NULL)):
            try:
                os.makedirs(os.path.dirname(str_NULL))
            except OSError as exc:  # Guard against race condition of path already existing
                if exc.errno != errno.EEXIST:
                    raise

        return str_NULL

    def load_data(self, input_file):
        Data = np.loadtxt(input_file, delimiter=",")
        (m, n) = Data.shape  # m: num of observations, n: size of observation vector
        print("completed getting the data")
        return Data, m, n

    def log_parameters(self):
        print("lam_sparse", self.lambda_parameter)
        print("switch_penalty", self.switch_penalty)
        print("num_cluster", self.number_of_clusters)
        print("num stacked", self.spatial_radius)

    def predict_clusters(self, test_data=None):
        '''
        Given the current trained model, predict clusters.  If the cluster segmentation has not been optimized yet,
        than this will be part of the interative process.

        Args:
            numpy array of data for which to predict clusters.  Columns are dimensions of the data, each row is
            a different timestamp

        Returns:
            vector of predicted cluster for the points
        '''
        if test_data is not None:
            if not isinstance(test_data, np.ndarray):
                raise TypeError("input must be a numpy array!")
        else:
            test_data = self.trained_model['complete_D_train']

        # SMOOTHENING
        lle_all_points_clusters = self.smoothen_clusters(self.trained_model['cluster_mean_info'],
                                                         self.trained_model['computed_covariance'],
                                                         self.trained_model['cluster_mean_stacked_info'],
                                                         test_data,
                                                         self.trained_model['spatial_series_col_size'])

        # Update cluster points - using NEW smoothening
        clustered_points = updateClusters(lle_all_points_clusters, switch_penalty=self.switch_penalty, spatial_series_index=self.spatial_series_index,
                                          spatial_series_closest=self.spatial_series_closest, spatial_radius=self.spatial_radius)

        return(clustered_points)
