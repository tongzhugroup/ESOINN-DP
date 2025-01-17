#!/usr/bin/env python
# coding=utf-8
from .DFTBcal import *
from ..Neuralnetwork import *
from ..Base import *
from ..Comparm import GPARAMS 
import numpy as np

def Cal_NN_EFQ(NNSet,inpath='./'):
    ERROR_mols=[]
    ERROR_strlist=[]
    MSet_list=[MSet('ID%d'%i) for i in range(len(GPARAMS.Esoinn_setting.NNdict['NN']))]
    Mol_label=[[] for i in NNSet.mols]
    if GPARAMS.Esoinn_setting.NNdict["Charge"]!=None:
        N_Times=math.ceil(len(NNSet.mols)/GPARAMS.Neuralnetwork_setting.Batchsize)
        QMCHARGE=[]
        for i in range(N_Times):
            TMMSET=MSet('tmp')
            TMMSET.mols=NNSet.mols[i*GPARAMS.Neuralnetwork_setting.Batchsize:(i+1)*GPARAMS.Neuralnetwork_setting.Batchsize]
#            try:
            atom_charge=\
                    Eval_charge(TMMSET,GPARAMS.Esoinn_setting.NNdict["Charge"])
#            except:
#                atom_charge=[]
            QMCHARGE+=list(atom_charge)
    for i in range(len(NNSet.mols)):
        for j in NNSet.mols[i].belongto:
            MSet_list[j].mols.append(NNSet.mols[i])
            Mol_label[i].append([j,len(MSet_list[j].mols)-1])
    E=[];F=[];Dipole=[];Charge=[]
    for i in range(len(GPARAMS.Esoinn_setting.NNdict["NN"])):
        if len(MSet_list[i].mols)>0:
            N_Times=math.ceil(len(MSet_list[i].mols)/GPARAMS.Neuralnetwork_setting.Batchsize)
            E_tmp=[];F_tmp=[];Dipole_tmp=[];Charge_tmp=[]
            for j in range(N_Times):
                TMMSET=MSet('tmp')
                TMMSET.mols=MSet_list[i].mols[j*GPARAMS.Neuralnetwork_setting.Batchsize:(j+1)*GPARAMS.Neuralnetwork_setting.Batchsize]
                #print ("NN Calculation at here!")
                #Etotal,Ebp,Ebp_atom,Ecc,Evdw,mol_dipole,atom_charge,gradient,hess=\
                Etotal,Ebp,Ebp_atom,Ecc,Evdw,mol_dipole,atom_charge,gradient=\
                    EvalSet(TMMSET,GPARAMS.Esoinn_setting.NNdict["NN"][i])
                #print ("NN Calculation at over!")
                E_tmp+=list(Etotal);F_tmp+=list(gradient);Dipole_tmp+=list(mol_dipole);Charge_tmp+=list(atom_charge)
            E.append(E_tmp)
            F.append(F_tmp)
            Dipole.append(Dipole_tmp)
            Charge.append(Charge_tmp)
        else:
            E.append([])
            F.append([])
            Dipole.append([])
            Charge.append([])
    MAX_ERR=[]
    NN_predict=[]
    for i,imol in enumerate(NNSet.mols):
        ERROR_str=''
        E_i=[];F_i=[];D_i=[];Q_i=[]
        for j in Mol_label[i]:
            E_i.append(E[j[0]][j[1]])
            F_i.append(F[j[0]][j[1]][0:len(imol.coords)])
            D_i.append(Dipole[j[0]][j[1]])
            Q_i.append(Charge[j[0]][j[1]][0:len(imol.coords)])
        E_i=np.array(E_i)*627.51
        F_i=np.array(F_i)*627.51/JOULEPERHARTREE
        D_i=np.array(D_i)
        Q_i=np.array(Q_i)
        NN_num=len(imol.belongto)
        if NN_num <=3:
            N_num=min(2,NN_num)
        else:
            N_num=math.ceil((NN_num+1)/2)
        E_avg=np.mean(E_i)
        F_avg=np.mean(F_i,axis=0)
        #tmp_list=np.argsort(np.max(np.reshape(np.square(F_i-F_avg),(len(imol.belongto),-1)),1))[:N_num]
        tmp_list=np.argsort(np.max(np.reshape(np.square(F_i-F_avg),(len(imol.belongto),-1)),1))
        F_New=[F_i[m] for m in tmp_list]
        F_avg=np.mean(F_New,axis=0)
        E_New=[E_i[m] for m in tmp_list]
        D_New=[D_i[m] for m in tmp_list]
        Q_New=[Q_i[m] for m in tmp_list]
        E_avg=np.mean(E_New)
        D_avg=np.mean(D_New,axis=0)
        Q_avg=np.mean(Q_New,axis=0)
        MSE_F=np.square(F_New-F_avg).mean(axis=0)
        MAX_MSE_F=-np.sort(-np.reshape(MSE_F,-1))[0]
        MAX_ERR.append(MAX_MSE_F)
        method='NN'
        if MAX_MSE_F >  GPARAMS.Train_setting.sigma**2 and MAX_MSE_F<(GPARAMS.Train_setting.sigma*3)**2:
            ERROR_str+='%s in NNSet is not believable, MAX_MSE_F: %f\n '%(imol.name,MAX_MSE_F)
            ERROR_strlist.append(ERROR_str)
            ERROR_mols.append([NNSet.mols[i],MAX_MSE_F])
        NN_predict.append([E_avg,F_avg,D_avg,Q_avg])

    if GPARAMS.Esoinn_setting.NNdict["Charge"]!=None:
        for i in range(len(NNSet.mols)):
            NN_predict[i][3]=QMCHARGE[i]
    return NN_predict,ERROR_mols,MAX_ERR,ERROR_strlist,method

