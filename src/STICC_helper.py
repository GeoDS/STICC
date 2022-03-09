import numpy as np


def getTrainTestSplit(m, num_blocks, num_stacked):
    '''
    - m: number of observations
    - num_blocks: spatial_radius + 1
    - num_stacked: spatial_radius
    Returns:
    - sorted list of training indices
    '''
    # Now splitting up stuff
    # split1 : Training and Test
    # split2 : Training and Test - different clusters
    training_percent = 1
    # list of training indices
    training_idx = np.random.choice(
        m-num_blocks+1, size=int((m-num_stacked)*training_percent), replace=False)
    # Ensure that the first and the last few points are in
    training_idx = list(training_idx)
    if 0 not in training_idx:
        training_idx.append(0)
    if m - num_stacked not in training_idx:
        training_idx.append(m-num_stacked)
    training_idx = np.array(training_idx)
    return sorted(training_idx)


def upperToFull(a, eps=0):
    ind = (a < eps) & (a > -eps)
    a[ind] = 0
    n = int((-1 + np.sqrt(1 + 8*a.shape[0]))/2)
    A = np.zeros([n, n])
    A[np.triu_indices(n)] = a
    temp = A.diagonal()
    A = np.asarray((A + A.T) - np.diag(temp))
    return A


def hex_to_rgb(value):
    """Return (red, green, blue) for the color given as #rrggbb."""
    lv = len(value)
    out = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    out = tuple([x/256.0 for x in out])
    return out


def updateClusters(LLE_node_vals, switch_penalty=1, spatial_series_index=[], spatial_series_closest=[], spatial_radius=1):
    """
    Takes in LLE_node_vals matrix and computes the path that minimizes
    the total cost over the path
    Note the LLE's are negative of the true LLE's actually!!!!!

    Note: switch penalty > 0
    """
    (T, num_clusters) = LLE_node_vals.shape
    future_cost_vals = np.zeros(LLE_node_vals.shape)

    # compute future costs
    for i in range(T-2, -1, -1):
        j = spatial_series_closest[i]  # find the closest
        j = int(j)
        indicator = np.zeros(num_clusters)
        if j <= (len(spatial_series_index) - spatial_radius):
            future_costs = future_cost_vals[j, :]
            lle_vals = LLE_node_vals[j, :]
            for cluster in range(num_clusters):
                total_vals = future_costs + lle_vals + switch_penalty
                total_vals[cluster] -= switch_penalty
                future_cost_vals[i, cluster] = np.min(total_vals)

    # compute the best path
    path = np.zeros(T)

    # the first location
    curr_location = np.argmin(future_cost_vals[0, :] + LLE_node_vals[0, :])
    path[0] = curr_location

    # compute the path
    for i in range(T-1):
        j = spatial_series_closest[i]  # find the closest
        j = int(j)
        if j <= (len(spatial_series_index) - spatial_radius):
            future_costs = future_cost_vals[j, :]
            lle_vals = LLE_node_vals[j, :]
            total_vals = future_costs + lle_vals + switch_penalty
            total_vals[int(path[i])] -= switch_penalty

        path[i+1] = np.argmin(total_vals)

    # return the computed path
    return path


def find_matching(confusion_matrix):
    """
    returns the perfect matching
    """
    _, n = confusion_matrix.shape
    path = []
    for i in range(n):
        max_val = -1e10
        max_ind = -1
        for j in range(n):
            if j in path:
                pass
            else:
                temp = confusion_matrix[i, j]
                if temp > max_val:
                    max_val = temp
                    max_ind = j
        path.append(max_ind)
    return path


def compute_confusion_matrix(num_clusters, clustered_points_algo, sorted_indices_algo):
    """
    computes a confusion matrix and returns it
    """
    seg_len = 400
    true_confusion_matrix = np.zeros([num_clusters, num_clusters])
    for point in range(len(clustered_points_algo)):
        cluster = clustered_points_algo[point]
        num = (int(sorted_indices_algo[point]/seg_len) % num_clusters)
        true_confusion_matrix[int(num), int(cluster)] += 1
    return true_confusion_matrix
