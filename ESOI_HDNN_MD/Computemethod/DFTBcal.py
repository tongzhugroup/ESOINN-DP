#!/usr/bin/env python
# coding=utf-8
from ..Base import *
from TensorMol import *
def Cal_DFTB_EFQ(NNSet,parapath,inpath):
    NN_predict=[];ERROR_mols=[]
    for i,imol in enumerate(NNSet.mols):
        NNSet.mols[i].Write_DFTB_input(parapath,False,inpath)
        NNSet.mols[i].Cal_DFTB(inpath)
        E_avg=NNSet.mols[i].properties['energy']*627.51
        F_avg=NNSet.mols[i].properties['force']*627.51
        D_avg=NNSet.mols[i].properties['dipole']
        Q_i=NNSet.mols[i].properties['charge']
        ERROR_mols.append(NNSet.mols[i])
        method='DFTB'
        NN_predict.append([E_avg,F_avg,D_avg,Q_i])
    return NN_predict,ERROR_mols,0,'',method
