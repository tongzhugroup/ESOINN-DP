from ..Comparm import *
import os

def productor(GPARAMS_index=0,Queue=None,GPUQueue=None):
    from ..Computemethod import QMMM_FragSystem
    from ..Computemethod import FullQM_System_Amber 
    from ..MD import Simulation
    from ..Base import Find_useable_gpu
    from ..LoadGPARAMS import LoadModel
    print (GPARAMS.Compute_setting.Traininglevel)
    print (GPARAMS.Compute_setting.Theroylevel)
#    os.environ["CUDA_VISIBLE_DEVICES"]=Find_useable_gpu(GPARAMS.Compute_setting.Gpulist)
    GPUid=GPUQueue.get()
    os.environ["CUDA_VISIBLE_DEVICES"]=str(GPUid)
    #os.environ["CUDA_VISIBLE_DEVICES"]='0'
    print (os.environ["CUDA_VISIBLE_DEVICES"])
    if GPARAMS.Compute_setting.Theroylevel=="DFTB+":
        os.environ["OMP_NUM_THREADS"]=GPARAMS.Compute_setting.Ncoresperthreads
    if GPARAMS.Compute_setting.Computelevel[GPARAMS_index]=="QM/MM":
        if GPARAMS.System_setting[GPARAMS_index].Forcefield=="Amber":
            prmfile=GPARAMS.System_setting[GPARAMS_index].Systemparm
            crdfile=GPARAMS.System_setting[GPARAMS_index].Initstruc 
            MDpath='./'+GPARAMS.MD_setting[GPARAMS_index].Name+'/'
            if not os.path.exists(MDpath):
                os.system("mkdir -p %s"%MDpath)
            os.system("cp "+prmfile+' '+MDpath+prmfile)
            os.system("cp "+crdfile+' '+MDpath+crdfile)
            if GPARAMS.MD_setting[GPARAMS_index].Stageindex!=0:
                print (GPARAMS.MD_setting[GPARAMS_index].Stageindex)
                if GPARAMS.MD_setting[GPARAMS_index].Ifcontinue==True:
                    restartstruc=GPARAMS.MD_setting[GPARAMS_index].Name+\
                        '_%d.rst7'%(GPARAMS.MD_setting[GPARAMS_index].Stageindex-1)
                else:
                    restartstruc=GPARAMS.MD_setting[GPARAMS_index].Name+'_0.inpcrd'
                initstruc=GPARAMS.MD_setting[GPARAMS_index].Name+\
                        '_%d.inpcrd'%(GPARAMS.MD_setting[GPARAMS_index].Stageindex)
                os.system('cp '+MDpath+restartstruc+' '+MDpath+initstruc)
            else:
                initstruc=GPARAMS.MD_setting[GPARAMS_index].Name+\
                        '_%d.inpcrd'%(GPARAMS.MD_setting[GPARAMS_index].Stageindex)
                pstruc=GPARAMS.System_setting[GPARAMS_index].Initstruc
                os.system("cp "+pstruc+' '+MDpath+initstruc)
            qmsys=QMMM_FragSystem(MDpath+prmfile,MDpath+initstruc,\
                                Strucdict=GPARAMS.System_setting[GPARAMS_index].Strucdict,\
                                Path=GPARAMS.MD_setting[GPARAMS_index].Name,\
                                Inpath='./'+GPARAMS.Compute_setting.Traininglevel+\
                                        '/'+GPARAMS.MD_setting[GPARAMS_index].Name+'/',\
                                 Name=GPARAMS.MD_setting[GPARAMS_index].Name,\
                                 chargelist=GPARAMS.System_setting[GPARAMS_index].reportcharge)
    elif GPARAMS.Compute_setting.Computelevel[GPARAMS_index]=="Full":
        if GPARAMS.System_setting[GPARAMS_index].Forcefield=="Amber":
            prmfile=GPARAMS.System_setting[GPARAMS_index].Systemparm
            crdfile=GPARAMS.System_setting[GPARAMS_index].Initstruc 
            MDpath='./'+GPARAMS.MD_setting[GPARAMS_index].Name+'/'
            if not os.path.exists(MDpath):
                os.system("mkdir -p %s"%MDpath)
            os.system("cp "+prmfile+' '+MDpath+prmfile)
            os.system("cp "+crdfile+' '+MDpath+crdfile)
            if GPARAMS.MD_setting[GPARAMS_index].Stageindex!=0:
                if GPARAMS.MD_setting[GPARAMS_index].Ifcontinue==True:
                    restartstruc=GPARAMS.MD_setting[GPARAMS_index].Name+\
                        '_%d.rst7'%(GPARAMS.MD_setting[GPARAMS_index].Stageindex-1)
                else:
                    restartstruc=GPARAMS.MD_setting[GPARAMS_index].Name+'_0.inpcrd'
                initstruc=GPARAMS.MD_setting[GPARAMS_index].Name+\
                        '_%d.inpcrd'%(GPARAMS.MD_setting[GPARAMS_index].Stageindex)
                os.system('cp '+MDpath+restartstruc+' '+MDpath+initstruc)
            else:
                initstruc=GPARAMS.MD_setting[GPARAMS_index].Name+\
                        '_%d.inpcrd'%(GPARAMS.MD_setting[GPARAMS_index].Stageindex)
                pstruc=GPARAMS.System_setting[GPARAMS_index].Initstruc
                os.system("cp "+pstruc+' '+MDpath+initstruc)
            qmsys=FullQM_System_Amber(MDpath+prmfile,MDpath+initstruc,\
                                          Path=GPARAMS.MD_setting[GPARAMS_index].Name,\
                                          Inpath='./'+GPARAMS.Compute_setting.Traininglevel+\
                                          '/'+GPARAMS.MD_setting[GPARAMS_index].Name+'/',\
                                        Name=GPARAMS.MD_setting[GPARAMS_index].Name\
                                         ) 
    if GPARAMS.MD_setting[GPARAMS_index].MDmethod=="Normal MD":
        print (GPARAMS.MD_setting[GPARAMS_index].Name)
        MD_simulation=Simulation(sys=qmsys,\
                                 MD_setting=GPARAMS.MD_setting[GPARAMS_index])

        try:
            MDdeviation=MD_simulation.MD(Queue)
        except Exception as e :
            print ("=======================================")
            print ("ERROR: MD of %s failed by some mistake!")
            print (e)
            print ("=======================================")

    GPUQueue.put(GPUid)
        

