import numpy as np
import pickle
import os,sys

def esoinn_train():
    from ..Comparm import GPARAMS 
    if len(GPARAMS.Esoinn_setting.Model.nodes)!=0: 
        cluster_center_before=GPARAMS.Esoinn_setting.Model.cal_cluster_center()
    else:
        cluster_center_before=None 

    with open(GPARAMS.Dataset_setting.ESOINNdataset,'rb') as f:
        Dataset=pickle.load(f)
        print ("Dataset len:", len(Dataset))

    try: 
        if GPARAMS.Esoinn_setting.scalemax==None and GPARAMS.Esoinn_setting.scalemin==None:
            GPARAMS.Esoinn_setting.scalemax=np.max(Dataset,0)
            GPARAMS.Esoinn_setting.scalemin=np.min(Dataset,0)
            Dataset=(Dataset-GPARAMS.Esoinn_setting.scalemin)/(GPARAMS.Esoinn_setting.scalemax-GPARAMS.Esoinn_setting.scalemin)
            Dataset[~np.isfinite(Dataset)]=0
            with open("Sfactor.in",'wb') as f:
                pickle.dump((GPARAMS.Esoinn_setting.scalemax,GPARAMS.Esoinn_setting.scalemin),f)
    except:
        pass 
    if len(GPARAMS.Esoinn_setting.Model.nodes)!=0:
        Noiseset,a,b,c,d=GPARAMS.Esoinn_setting.Model.predict(Dataset)
    else:
        Noiseset=Dataset  
    GPARAMS.Esoinn_setting.Model.fit(Noiseset,iteration_times=GPARAMS.Train_setting.Esoistep,if_reset=False)
    GPARAMS.Esoinn_setting.Model.Save()
    with open(GPARAMS.Dataset_setting.ESOINNdataset,'wb') as f:
        pickle.dump(Dataset,f)
    cluster_center_after=GPARAMS.Esoinn_setting.Model.cal_cluster_center()
    if cluster_center_before!=None:# and GPARAMS.Esoinn_setting.NNdict["NN"]!=None:
        print ("Update HDNN")
        #print (cluster_center_before)
        updaterule=np.zeros(GPARAMS.Esoinn_setting.Model.class_id)
        for i in range(len(cluster_center_after)):
            vec1=cluster_center_after[i]
            dis=np.sum((np.array(cluster_center_before)-np.array([vec1]*len(cluster_center_before)))**2,1) 
            index=np.argmin(dis)
            print (i,index,"+++++++++++++++++++++++++++")
            updaterule[i]=index 
        os.system("mkdir -p ./networks/lastsave")
        os.system("mv ./networks/%s* ./networks/lastsave"%GPARAMS.Esoinn_setting.efdnetname) 
        os.system("rm `find -name events*`")
        for i in range(len(cluster_center_after)):
            snetname=GPARAMS.Esoinn_setting.efdnetname+"%d_ANI1_Sym_Direct_RawBP_EE_Charge_DipoleEncode_Update_vdw_DSF_elu_Normalize_Dropout_0"%updaterule[i]
            tnetname=GPARAMS.Esoinn_setting.efdnetname+"%d_ANI1_Sym_Direct_RawBP_EE_Charge_DipoleEncode_Update_vdw_DSF_elu_Normalize_Dropout_0"%i
            os.system("cp ./networks/lastsave/%s.tfn  ./networks/%s.tfn"%(snetname,tnetname))
            os.system("cp ./networks/lastsave/%s ./networks/%s -r"%(snetname,tnetname))
            for j in ['.index','.meta','.data-00000-of-00001']:
                os.system('mv ./networks/%s/%s-chk%s ./networks/%s/%s-chk%s'%(tnetname,snetname,j,tnetname,tnetname,j))
        
        


