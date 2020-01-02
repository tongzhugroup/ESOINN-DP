import numpy as np
import pickle
import random
from multiprocessing import Queue,Process,Manager
from ..Neuralnetwork import *
from ..Comparm import *
from math import *
import paramiko as pko     
from .Jobqueue import lsfgpustr 
def trainer(DataQueue,GPUQueue=None,jsonfile=''):
    from   TensorMol import MSet,PARAMS,MolDigester
    import os
    from ..Base import Find_useable_gpu
    if GPARAMS.Train_setting.Ifgpuwithhelp==False:
        GPUid=GPUQueue.get()
        os.environ["CUDA_VISIBLE_DEVICES"]=str(GPUid)
    TMMSET,ider,maxsteps=DataQueue.get()
    print ("OOOOOOOOOOOOXXXXXXXXXXXXXXXXXXXXXOOOOOOOOOOOOOOOOO")
    print ("Name:",TMMSET.name,ider)
    if len(TMMSET.mols)< GPARAMS.Neuralnetwork_setting.Batchsize*20 :
        num=math.ceil(GPARAMS.Neuralnetwork_setting.Batchsize*20/len(TMMSET.mols))
        TMMSET.mols=TMMSET.mols*num
    if GPARAMS.Train_setting.Ifgpuwithhelp==False:
        print ("Visible CPU ID: %s training Cluster %d subnet"\
           %(os.environ["CUDA_VISIBLE_DEVICES"],ider))
    if len(GPARAMS.Neuralnetwork_setting.NNstrucsele11yyct)!=0:
        candidate_struc=get_best_struc(2)
        print ("Candidate_NNSTRUC:",candidate_struc) 
        basestruc=[math.ceil(i) for i in np.mean(candidate_struc,axis=0)] 
    else:
        basestruc=GPARAMS.Neuralnetwork_setting.Initstruc 
    deltastruc=[math.ceil(i*0.10) for i in basestruc]
    print("Delta struc:",deltastruc)
    changevector=[random.randint(-5,5) for i in range(3)]
    evostruc=[basestruc[i]+deltastruc[i]*changevector[i] for i in range(3)]
    print("evo struc:",evostruc)
    #try:
    if GPARAMS.Train_setting.Ifgpuwithhelp==False:
        TreatedAtoms=TMMSET.AtomTypes()
        d=MolDigester(TreatedAtoms,name_="ANI1_Sym_Direct",OType_="EnergyAndDipole")
        tset=TData_BP_Direct_EE_WithEle(TMMSET,d,order_=1,num_indis_=1,type_="mol",WithGrad_=True,MaxNAtoms=100)
        NN_name=None 
        ifcontinue=False
        SUBNET=BP_HDNN(tset,NN_name,Structure=evostruc)
        print (SUBNET.max_steps)
        try:
            Ncase,batchnumf,Lossf,Losse,batchnumd,Lossd,structure=SUBNET.train(SUBNET.max_steps,continue_training=ifcontinue)
            strucstr=" ".join([str(i) for i in structure])
            NNstrucfile=open(GPARAMS.Neuralnetwork_setting.NNstrucrecord,'a')
            NNstrucfile.write("%d, %d, %f, %f, %d, %f, %s,\n"\
                        %(Ncase,batchnumf,Lossf,Losse,batchnumd,Lossd,strucstr))
        except:
            SUBNET.SaveAndClose()
        GPUQueue.put(GPUid)
    else:
        trans=pko.Transport((GPARAMS.Train_setting.helpgpunodeip,GPARAMS.Train_setting.helpgpuport))
        trans.connect(username=GPARAMS.Train_setting.helpgpuaccount,password=GPARAMS.Train_setting.helpgpupasswd)
        ssh=pko.SSHClient()
        ssh._transport=trans
        sftp=pko.SFTPClient.from_transport(trans)
        workpath=os.getcwd()
        print (workpath)
        MSetname=TMMSET.name
        remotepath=GPARAMS.Train_setting.helpgpupath+'/Stage%d/Cluster%d'%(GPARAMS.Train_setting.Trainstage,ider)
        srcpath=workpath+'/datasets/%s.pdb'%(MSetname)
        print (remotepath,srcpath)
        stdin,stdout,stderr=ssh.exec_command('rm %s'%(remotepath))
        stdin,stdout,stderr=ssh.exec_command('mkdir -p %s'%(remotepath+'/datasets'))
        print (stdout.read().decode())
        sftp.put(srcpath,remotepath+'/datasets/%s.pdb'%(MSetname))
        if GPARAMS.Train_setting.gpuqueuetype=='LSF':
            lsfrun=open('lsf_gpu%d.run'%ider,'w')
            lsfrun.write(lsfgpustr%(GPARAMS.Train_setting.gpuqueuename,'Cluster%d'%ider))
            print(lsfgpustr%(GPARAMS.Train_setting.gpuqueuename,'Cluster%d'%ider),TMMSET.name,ider)
            lsfrun.write(GPARAMS.Train_setting.helpgpuenv)
            strucstr="_".join([str(i) for i in evostruc])
            lsfrun.write('TrainNN.py -i %s -d %s -s %s -t bp\n'%(jsonfile,MSetname,strucstr))
            lsfrun.write('touch finished\n')
            lsfrun.close()
            sftp.put(localpath=workpath+'/lsf_gpu%d.run'%ider,remotepath=remotepath+'/lsf_gpu.run')
            sftp.put(localpath=workpath+'/%s'%jsonfile,remotepath=remotepath+'/%s'%jsonfile)
            stdin,stdout,stderr=ssh.exec_command("cd %s && bsub <lsf_gpu.run"%remotepath)
            flag=True 
            while flag:
                stdin,stdout,stderr=ssh.exec_command("cd %s&& ls"%remotepath)
                tmpstr=stdout.read().decode()
                flag=not ('finished' in tmpstr)
            stdin,stdout,stderr=ssh.exec_command("cd %s && mv %s/*.record networks/Cluster%d.record"%(remotepath,remotepath,ider))
            print (stdout.read().decode())
            stdin,stdout,stderr=ssh.exec_command("cd %s && tar zcvf Cluster%d.tar.gz networks/*"%remotepath)
            print (stdout.read().decode())
            sftp.get(localpath=workpath+'/networks/Cluster%d.tar.gz'%ider,\
                    remotepath=remotepath+'/networks/Cluster%d.tar.gz'%ider)
            sftp.get(localpath=workpath+'/tmp.record',remotepath=remotepath+'/NNstruc.record')
            os.system('cat tmp.record >> NNstruc.record')
            os.system('cd ./networks && tar zxvf Cluster%d.tar.gz && mv *.record %s/Stage%d/'%(ider,GPARAMS.Compute_setting.Traininglevel,GPARAMS.Train_setting.Trainstage))
            os.system('rm lsf_*.run')
def get_best_struc(candidate_num):
    score=np.zeros(len(GPARAMS.Neuralnetwork_setting.NNstrucselect))
    floss=[i[2][0] for i in GPARAMS.Neuralnetwork_setting.NNstrucselect]
    dloss=[i[2][2] for i in GPARAMS.Neuralnetwork_setting.NNstrucselect]
    fspeed=[i[1][0] for i in GPARAMS.Neuralnetwork_setting.NNstrucselect]
    dspeed=[i[1][1] for i in GPARAMS.Neuralnetwork_setting.NNstrucselect]
    flosssort=np.argsort(floss)
    dlosssort=np.argsort(dloss)
    fspeedsort=np.argsort(fspeed)
    dspeedsort=np.argsort(dspeed)
    for i in range(len(GPARAMS.Neuralnetwork_setting.NNstrucselect)):
        score[flosssort[i]]+=i
        score[dlosssort[i]]+=i
        score[fspeedsort[i]]+=i
        score[dspeedsort[i]]+=i
    scoresort=np.argsort(score)[:2]
    print("score:",score)
    print ("scoresort:",scoresort)
    candidate_struc=[GPARAMS.Neuralnetwork_setting.NNstrucselect[i][3] for i in scoresort]
    print (np.mean(candidate_struc,axis=0))
    return candidate_struc
def respnet_train(MSetname,GPUQueue):
    if GPARAMS.Train_setting.Ifgpuwithhelp==False:
        print ("Visible CPU ID: %s training Cluster %d subnet"\
           %(os.environ["CUDA_VISIBLE_DEVICES"],ider))
    if len(GPARAMS.Neuralnetwork_setting.NNstrucsele11yyct)!=0:
        candidate_struc=get_best_struc(2)
        print ("Candidate_NNSTRUC:",candidate_struc) 
        basestruc=[math.ceil(i) for i in np.mean(candidate_struc,axis=0)] 
    else:
        basestruc=GPARAMS.Neuralnetwork_setting.Initstruc 
    deltastruc=[math.ceil(i*0.10) for i in basestruc]
    print("Delta struc:",deltastruc)
    changevector=[random.randint(-5,5) for i in range(3)]
    evostruc=[basestruc[i]+deltastruc[i]*changevector[i] for i in range(3)]
    print("evo struc:",evostruc)
    if GPARAMS.Train_setting.Ifgpuwithhelp==False:
        GPUID=GPUQueue.get()
        os.environ["CUDA_VISIBLE_DEVICES"]=str(GPUID) 
        Respset=MSet("HF_resp")
        Respset.Load()
        GPARAMS.Neuralnetwork_setting.Switchrate=0.9
        if len(Respset.mols)<GPARAMS.Neuralnetwork_setting.Batchsize*20:
            num=math.ceil(GPARAMS.Neuralnetwork_setting.Batchsize*20/len(TMPset.mols))
            Respset.mols=Respset.mols*num
        TreatedAtoms=Respset.AtomTypes()
        d=MolDigester(TreatedAtoms,name_="ANI1_Sym_Direct", OType_="EnergyAndDipole")
        tset=TData_BP_Direct_EE_WithCharge(Respset,d,order_=1,num_indis_=1,type_="mol",WithGrad_=True,MaxNAtoms=100)
        NN_name=None
        ifcontinue=False
        SUBNet=BP_HDNN_charge(tset,NN_name,Structure=evostruc)
        SUBNet.train(SUBNet.max_steps,continue_training=ifcontinue)
        GPUQueue.put(GPUid)
    else:
        trans=pko.Transport((GPARAMS.Train_setting.helpgpunodeip,GPARAMS.Train_setting.helpgpuport))
        trans.connect(username=GPARAMS.Train_setting.helpgpuaccount,password=GPARAMS.Train_setting.helpgpupasswd)
        ssh=pko.SSHClient()
        ssh._transport=trans
        sftp=pko.SFTPClient.from_transport(trans)
        workpath=os.getcwd()
        print (workpath)
        remotepath=GPARAMS.Train_setting.helpgpupath+'/Stage%d/resp'%(GPARAMS.Train_setting.Trainstage)
        srcpath=workpath+'/datasets/%s.pdb'%(MSetname)
        print (remotepath,srcpath)
        stdin,stdout,stderr=ssh.exec_command('rm %s'%(remotepath))
        stdin,stdout,stderr=ssh.exec_command('mkdir -p %s'%(remotepath+'/datasets'))
        print (stdout.read().decode())
        sftp.put(srcpath,remotepath+'/datasets/%s.pdb'%(MSetname))
        if GPARAMS.Train_setting.gpuqueuetype=='LSF':
            lsfrun=open('lsf_gpu%d.run'%ider,'w')
            lsfrun.write(lsfgpustr%(GPARAMS.Train_setting.gpuqueuename,'Resp'))
            print(lsfgpustr%(GPARAMS.Train_setting.gpuqueuename,'Resp'),MSetname)
            lsfrun.write(GPARAMS.Train_setting.helpgpuenv)
            strucstr="_".join([str(i) for i in evostruc])
            lsfrun.write('TrainNN.py -i %s -d %s -s %s -t bpresp \n'%(jsonfile,MSetname,strucstr))
            lsfrun.write('touch finished\n')
            lsfrun.close()
            sftp.put(localpath=workpath+'/lsf_gpu%d.run'%ider,remotepath=remotepath+'/lsf_gpu.run')
            sftp.put(localpath=workpath+'/%s'%jsonfile,remotepath=remotepath+'/%s'%jsonfile)
            stdin,stdout,stderr=ssh.exec_command("cd %s && bsub <lsf_gpu.run"%remotepath)
            flag=True 
            while flag:
                stdin,stdout,stderr=ssh.exec_command("cd %s&& ls"%remotepath)
                tmpstr=stdout.read().decode()
                flag=not ('finished' in tmpstr)
            stdin,stdout,stderr=ssh.exec_command("cd %s && mv %s/*.record networks/resp.record"%(remotepath,remotepath,ider))
            print (stdout.read().decode())
            stdin,stdout,stderr=ssh.exec_command("cd %s && tar zcvf resp.tar.gz networks/*"%remotepath)
            print (stdout.read().decode())
            sftp.get(localpath=workpath+'/networks/resp.tar.gz'%ider,\
                    remotepath=remotepath+'/networks/resp.tar.gz'%ider)
            sftp.get(localpath=workpath+'/tmp.record',remotepath=remotepath+'/NNstruc.record')
            os.system('cat tmp.record >> NNstruc.record')
            os.system('cd ./networks && tar zxvf resp.tar.gz && mv *.record %s/Stage%d/'%(GPARAMS.Compute_setting.Traininglevel,GPARAMS.Train_setting.Trainstage))
            os.system('rm lsf_*.run')
    return 

