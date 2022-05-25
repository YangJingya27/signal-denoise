import pandas as pd
import cv2
import os
import numpy as np
from itertools import product
import argparse


"""
x = N(u,C)
y = Hx+\eta 
H=I, \eta=N(0,\Gamma_obs)


paras_nums = hypers['mu_nums']*hypers['gamma_nums']*hypers['d_nums']##*hypers['noise_num']
samples_nums = paras_nums*hypers['M_samples_per_para']

Returns  
-------
thetas [samples_nums,para_dim]
    xs [samples_nums,x_dim]          x_dim =hypers['image_size']**2
    ys [samples_nums,data_dim]    data_dim = x_dim
"""
parser = argparse.ArgumentParser(description='give parallel nodes, max=all_nodes*0.5')
parser.add_argument('--parall_nodes', type=int, default=2, help='parallel nodes, need to be less than all_nodes*0.5')
parser.add_argument('--bin_num_total', type=int, default=5, help='split all parameters into bin_num_total group')
parser.add_argument('--bin_num', type=int, default=0, help='simulate data for bin_num th groups parameters, 0<=bin_num<bin_num_total')
args = parser.parse_args()

# %%
if __name__ == "__main__":
    from problem_setting import *
    from pathos.pools import ProcessPool


    def gen_one_para_samples(theta, hypers=hypers):
        """
        x = N(0,C);b=N(0,sigma^2)
        y = Hx+b,
        shape:H[n*x_dim]; x[x_dim,1]; b[n,1]; y[n,1]
        shape_:H[n*x_dim]; x[M,x_dim]; b[M,1]  y[M,n]
            Parameters
            ----------
                 theta: [sigma]
                 ####### [mu,gamma,d,sigma]
                hypers:

            Returns
                thetas, xs, ys:  [M,dim]
            -------

        """
        H = hypers['H']
        M = hypers['M_samples_per_para']
        x_dim = hypers['x_dim']
        sigma_noise = theta
        C = np.identity(x_dim) * (hypers['sigma_prior']**2)
        xs = np.random.multivariate_normal([0] * x_dim, C, M) # [M,x_dim]
        b = np.random.randn(M,1) * sigma_noise
        ys = xs + b
        return np.array([theta] * M), xs, ys

    # range of hypers #??
    # sigmas_noise = np.linspace(hypers['sigma_range'][0], hypers['sigma_range'][1], hypers['noise_num']).round(5)
    sigmas_noise = np.array(hypers['sigma_range'])
    thetas_all = np.array(list(sigmas_noise)).reshape(-1,1)
    print(thetas_all.shape)

    # parallel
    pool = ProcessPool(nodes=args.parall_nodes)
    thetas_parts = np.array_split(thetas_all, args.bin_num_total)
    for _ in range(1):
        # data_file
        data_file = hypers['data_file_prefix'] + f'_{args.bin_num}.npz'
        print(f"simulate samples:{data_file}")
        
        theta_part = thetas_parts[args.bin_num]
        data_all = pool.map(gen_one_para_samples, theta_part)
        #         paras_nums = hypers['mu_nums'] * hypers['gamma_nums'] * hypers['noise_num']
        paras_nums = len(theta_part)  #??
        thetas = np.empty((paras_nums, hypers['M_samples_per_para'], 1)) #??
        xs = np.empty((paras_nums, hypers['M_samples_per_para'], hypers['x_dim']))
        ys = np.empty((paras_nums, hypers['M_samples_per_para'], hypers['data_dim']))

        for i, (thetas_i, xs_i, ys_i) in enumerate(data_all):
            thetas[i], xs[i], ys[i] = thetas_i, xs_i, ys_i
            if i%100==0:
                print('已循环'+str(i)+'次')

        thetas = thetas.reshape(-1, 1) #??
        xs = xs.reshape(-1, hypers['x_dim'])
        ys = ys.reshape(-1, hypers['data_dim'])
        
        np.savez(data_file, thetas=thetas, xs=xs, ys=ys)
        print(f"saved samples:{data_file}")
        







