import torch
import numpy as np
from scipy.cluster.vq import kmeans2


def initialize_inducing(model, data_ys, ts_max, data_noise=1e-1):
    """
    Initialization of inducing variables for a GPODE model
    Inducing locations are initialized at cluster centers
    Inducing values are initialized using empirical data gradients.

    @param model: a gpode.SequenceModel object
    @param data_ys: observed sequence (N,T,D)
    @param ts_max: max observation time, observations are assumed to start at time=0.
    @param data_noise: an initial guess for observation noise.
    @return: the model object after initialization
    """

    # compute empirical gradients and scale them according to observation time.
    f_xt = data_ys[:, 1:, :] - data_ys[:, :-1, :]  # (N,T-1,D)
    f_xt = f_xt.reshape(-1, data_ys.shape[-1]) * (data_ys.shape[1] / ts_max)  # (N,T-1,D)
    data_ys = data_ys[:, :-1, :]  # (N,T-1,D)
    data_ys = data_ys.reshape(-1, data_ys.shape[-1])  # (N*T-1,D)

    with torch.no_grad():
        num_obs_for_initialization = np.minimum(1000, data_ys.shape[0])
        obs_index = np.random.choice(data_ys.shape[0], num_obs_for_initialization, replace=False)

        inducing_loc = torch.tensor(kmeans2(data_ys, k=model.flow.odefunc.diffeq.Um().shape[0], minit='points')[0])
        data_ys = torch.tensor(data_ys[obs_index])
        f_xt = torch.tensor(f_xt[obs_index])

        Kxx = model.flow.odefunc.diffeq.kern.K(data_ys)  # (N,N) or (D,N,N)
        Kxz = model.flow.odefunc.diffeq.kern.K(data_ys, inducing_loc)  # (N,M) or (D,N,M)
        Kzz = model.flow.odefunc.diffeq.kern.K(inducing_loc)  # (M,M) or (D,M,M)
        Lxx = torch.cholesky(Kxx + torch.eye(Kxx.shape[1]) * data_noise)  # (N,N) or (D,N,N)
        Lzz = torch.cholesky(Kzz + torch.eye(Kzz.shape[1]) * 1e-4 * Kzz.shape[0])  # (M,M) or (D,M,M)

        if not model.flow.odefunc.diffeq.dimwise:
            alpha = torch.triangular_solve(f_xt, Lxx, upper=False)[0]  # (N,D)
            alpha = torch.triangular_solve(alpha, Lxx.T, upper=True)[0]  # (N,D)
            f_update = torch.einsum('nm, nd -> md', Kxz, alpha)  # (M,D)
        else:
            alpha = torch.triangular_solve(f_xt.T.unsqueeze(2), Lxx, upper=False)[0]  # (N,D)
            alpha = torch.triangular_solve(alpha, Lxx.permute(0, 2, 1), upper=True)[0]  # (N,D)
            f_update = torch.einsum('dnm, dn -> md', Kxz, alpha.squeeze(2))  # (M,D)

        inducing_val = torch.triangular_solve(f_update.T.unsqueeze(2), Lzz, upper=False)[0].squeeze(2).T  # (M,D)

        model.flow.odefunc.diffeq.inducing_loc().data = inducing_loc.data  # (M,D)
        model.flow.odefunc.diffeq.Um().data = inducing_val.data  # (M,D)
        return model


def initialize_latents_with_data(model, data_ys, data_ts, num_samples=20):
    """
    Initializes latent state distribution (or only initial state distribution) from data.
    Initial state distribution is initialized by solving the ODE backward in time from the first
        observation after inducing variables are initialized.

    @param model: a gpode.SequenceModel object
    @param data_ys: observed state sequence
    @param data_ts: observed time sequence
    @param num_samples: number of samples to consider for initial state initialization
    @return: the model object after initialization
    """
    with torch.no_grad():
        ts = torch.tensor(data_ts)
        init_xs = torch.tensor(data_ys[:, :-1])
        init_ts = torch.cat([ts[1:2], ts[0:1]])
        init_x0 = []
        for _ in range(num_samples):
            init_x0.append(model.build_flow(init_xs[:, 0], init_ts).clone().detach().data[:, -1])
        init_x0 = torch.stack(init_x0).mean(0)
        model.x0_distribution._initialize(init_x0)
    return model
