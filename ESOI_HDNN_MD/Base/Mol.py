#from TensorMol import * 
from .Physics import *
from .Dftbin import *
from ..Comparm import GPARAMS 
from ..Comparm import * 
import numpy as np
import time
class Molnew:
    def __init__(self,atoms=np.array([1],dtype=int),crd=np.array([0.0,0.0,0.0],dtype=float),charge=np.array([0.0],dtype=float)):
        #Mol.__init__(self,atoms,crd)
        self.atoms=atoms
        self.atomnamelist=[Element_Table[i] for i in self.atoms]
        print (self.atomnamelist)
        self.coords=crd 
        self.totalcharge=charge
        self.natom=len(atoms)
        self.name=time.strftime("%d-%H-%M-%S_mol", time.localtime()) 
        self.properties={}
        self.belongto=[]
    def Update_from_Gaulog(self,filename):
        file=open(filename,'r') 
        line=file.readline()
        natom=0
        atoms=[];coords=[];charge=[];force=[];dipole=[];energy=0
        while line:
            if 'Charge' in line and 'Multiplicity' in line:
                var=line.split()
                totalcharge=int(var[2]);spin=int(var[-1])
            if 'Coordinates (Angstroms)' in line:
                line=file.readline()
                line=file.readline()
                line=file.readline()
                while '--------------------------' not in line:
                    var=line.split()
                    atoms.append(int(var[1]))
                    coords.append([float(var[3]),float(var[4]),float(var[5])])
                    natom=natom+1
                    line=file.readline()
                    
            if 'Hirshfeld charges,' in line:
                line=file.readline()
                line=file.readline()
                while not('Tot' in line):
                    var=line.split()
                    charge.append(float(var[2]))
                    line=file.readline()
            if 'SCF Done' in line:
                var=line.split()
                energy=float(var[4])
            if 'ESP charges:' in line:
                line=file.readline()
                line=file.readline()
                while not('Sum of ESP' in line):
                    var=line.split()
                    charge.append(float(var[2]))
                    line=file.readline()
            if 'Forces (Hartrees/Bohr)' in line:
                line=file.readline()
                line=file.readline()
                line=file.readline()
                while not('------' in line):
                    var=line.split()
                    force.append([float(var[2])/0.529,\
                                float(var[3])/0.529,float(var[4])/0.529])
                    line=file.readline()
            if 'Predicted change' in line:
                DBLOCK=''
                while 'Normal termination' not in line:
                    if 'Error termination' in line:
                        print (filename+' is end with error')
                        stop
                    DBLOCK=DBLOCK+line.strip('\n').strip()
                    line=file.readline()
                var=DBLOCK.split('\\')
                for i in var:
                    if 'Dipole' in i:
                        dipole_str=i.strip(' Dipole=')
                        print (filename,dipole_str)
                        dipole=[float(m)/0.393456 for m in dipole_str.split(',')]
            line=file.readline()
        self.atoms=np.array(atoms)
        self.coords=np.array(coords) 
        self.Total_charge=totalcharge
        self.properties['energy']=energy
        self.properties['force']=np.array(force)
        self.properties['gradients']=-np.array(force)
        self.properties['dipole']=np.array(dipole)
        self.properties['charge']=np.array(charge)
        
    def Cal_EGCM(self,dummy_water=1):
        anum=len(self.atoms)
        crd=self.coords
        element_list=self.atoms 
        train_crd=np.zeros((GPARAMS.Esoinn_setting.Maxnum,3),dtype=float)
        Mask=np.zeros(GPARAMS.Esoinn_setting.Maxnum,dtype=float)
        Tnatom=np.zeros(len(GPARAMS.Esoinn_setting.Atype),dtype=int)
        for i in range(anum):
            for j in range(len(GPARAMS.Esoinn_setting.Atype)):
                if element_list[i]==GPARAMS.Esoinn_setting.Atype[j]:
                    train_crd[GPARAMS.Esoinn_setting.Apt[j][0]+Tnatom[j]]=crd[i]
                    Mask[GPARAMS.Esoinn_setting.Apt[j][0]+Tnatom[j]]=1.0
                    Tnatom[j]=Tnatom[j]+1
        dummy_list=[[] for m in GPARAMS.Esoinn_setting.Atype]
        for i in range(GPARAMS.Esoinn_setting.Maxnum):
            if Mask[i]==0:
                for j in range(len(GPARAMS.Esoinn_setting.Atype)):
                    if GPARAMS.Esoinn_setting.Eindex[i]==GPARAMS.Esoinn_setting.Atype[j]:
                        dummy_list[j].append(i)
        C=np.zeros((len(train_crd),len(train_crd)),dtype=float)
        for i in range(len(train_crd)):
            for j in range(len(train_crd)):
                if i==j :
                    C[i][j]=0.5*GPARAMS.Esoinn_setting.Eindex[i]**2.4
                if i!=j and Mask[i]!=0 and Mask[j]!=0:
                    R=np.sqrt(np.sum((train_crd[i]-train_crd[j])**2))
                    C[i][j]=GPARAMS.Esoinn_setting.Eindex[i]*GPARAMS.Esoinn_setting.Eindex[j]/R
        if dummy_water==1:
            O_index=GPARAMS.Esoinn_setting.Atype.index(8);H_index=GPARAMS.Esoinn_setting.Atype.index(1)
            if len(dummy_list[O_index])>0 and len(dummy_list[H_index])>0:
                _,dummy_water_mod=np.divmod(len(dummy_list[H_index]),len(dummy_list[O_index]))
                if dummy_water_mod==0:
                    dummy_water_num=len(dummy_list[O_index])
                    for i in range(dummy_water_num):
                        C[dummy_list[O_index][i]][dummy_list[H_index][2*i]]=8.0/0.96
                        C[dummy_list[H_index][2*i]][dummy_list[O_index][i]]=8.0/0.96
                        C[dummy_list[O_index][i]][dummy_list[H_index][2*i+1]]=8.0/0.96
                        C[dummy_list[H_index][2*i+1]][dummy_list[O_index][i]]=8.0/0.96
                        C[dummy_list[H_index][2*i+1]][dummy_list[H_index][2*i]]=1.0/1.56795
                        C[dummy_list[H_index][2*i]][dummy_list[H_index][2*i+1]]=1.0/1.56795
        CoulombMatrix=C
        self.EGCM,EVEC=np.linalg.eig(CoulombMatrix)
        self.EGCM=np.sort(-self.EGCM)
        return self.EGCM
    def Write_DFTB_input(self,para_path,ifsave,inpath='./'):
        DFTBhubdict={'N':-0.1535,'H':-0.1857,'C':-0.1492,'S':-0.1100,'O':-0.1575,'Zn':-0.03}
        Symbol2num={'Zn':30,'N':7,'H':1,'C':6,'O':8,'Mg':12,'Ca':20,'Na':11,'K':19,'S':16}
        Num2Symbol={1:'H',6:'C',7:'N',8:'O',11:'Na',12:'Mg',13:'Al',16:'S',19:'K',20:'Ca',29:'Cu',30:'Zn'}
        Orbdict={'N':'p','H':'s','C':'p','S':'d','O':'p','Zn':'d'} 
        self.typedict={}
        self.typenumdict={}
        self.typenum=0
        self.typearray=np.zeros(self.natom,dtype=int)
        self.center_coords=np.zeros(3)
        for i in range(self.natom):
            if self.atoms[i] not in self.typedict.keys():
                self.typenum+=1
                self.typedict[self.atoms[i]]=self.typenum
                self.typenumdict[self.typenum]=self.atoms[i]
            self.typearray[i]=self.typedict[self.atoms[i]]
            if self.atoms[i]==30:
                center_coords=self.coords[i]
        self.coords=self.coords-center_coords
        typestr='';hubstr='';orbitalstr=''
        for i in range(self.typenum):
            typestr=typestr+Num2Symbol[self.typenumdict[i+1]]+' '
            symbol=Num2Symbol[self.typenumdict[i+1]]
            hubstr=hubstr+'\t%s=%.4f\n'%(symbol,DFTBhubdict[symbol])
            orbitalstr=orbitalstr+'\t%s="%s"\n'%(symbol,Orbdict[symbol])
        DFTB_cstr=''
        DFTB_cstr+='%d   C\n'%self.natom
        DFTB_cstr+='%s\n'%typestr
        for i in range(self.natom):
            DFTB_cstr+='%d   %d   %.6f\t%.6f\t%.6f\n'%(i+1,self.typearray[i],self.coords[i][0],self.coords[i][1],self.coords[i][2])
        if ifsave==True:
            DFTB_input=open(path+self.name+'.dftbin','w')
            DFTB_input.write(DFTBin%(DFTB_cstr,para_path,orbitalstr,self.totalcharge,hubstr))
            DFTB_input.close()
        
        DFTB_input=open(inpath+'dftb_in.hsd','w')
        DFTB_input.write(DFTBin%(DFTB_cstr,para_path,orbitalstr,self.totalcharge,hubstr))
        DFTB_input.close()
    def Cal_DFTB(self,inpath='./'):
        if inpath!='./':
            print ('cd %s && dftb+ > dftb+.log'%inpath)
            os.system('cd %s && dftb+ > dftb+.log'%inpath)
        else:
            print ('cd %s && dftb+ > dftb+.log')
            os.system('dftb+ > dftb+.log') 
        flag=os.path.isfile(inpath+'detailed.out')
        if flag==True:
            outfile=open(inpath+'detailed.out','r')
            line=outfile.readline()
            force=[];charge=[]
            while line:
                if 'Total energy:' in line:
                    var=line.split()
                    energy=float(var[2])
                if 'Total Forces' in line:
                    for i in range(self.natom):
                        line=outfile.readline()
                        var=line.split()
                        force.append([float(var[0])/0.529,float(var[1])/0.529,float(var[2])/0.529])
                if 'Atomic gross charges (e)' in line:
                    line=outfile.readline()
                    for i in range(self.natom):
                        line=outfile.readline()
                        var=line.split()
                        charge.append(float(var[-1]))
                if 'Dipole moment:' in line and 'Debye' in line:
                    var=line.split()
                    Dipole=[float(var[2]),float(var[3]),float(var[4])]
                line=outfile.readline()
            outfile.close()
            force=np.array(force)
            charge=np.array(charge)
            self.properties["energy"]=energy
            self.CalculateAtomization('DFTB')
            print (self.properties["atomization"])
            self.properties["force"]=force
            self.properties["gradients"]=-force
            try:
                self.properties["dipole"]=np.array(Dipole)
            except:
                self.properties["dipole"]=np.zeros(3)
            self.properties["charge"]=charge
        return flag  

    def CalculateAtomization(self,Level):
        if (Level=='DFTB3'):
            AE = self.properties["energy"]
            for i in range (0, self.atoms.shape[0]):
                if (self.atoms[i] in DFTB3_U):
                    AE = AE - DFTB3_U[self.atoms[i]]
            self.properties["atomization"] = AE
            
        elif (Level=='REAXFF'):
            AE=self.properties["energy"]
            for i in range(0,self.atoms.shape[0]):
                if (self.atoms[i] in reax_U):
                    AE = AE - reax_U[self.atoms[i]]
            self.properties["atomization"]=AE
        elif (Level=='M062X/SDD'):
            AE=self.properties["energy"]
            for i in range(0,self.atoms.shape[0]):
                if (self.atoms[i] in M062XSDD_U):
                    AE = AE - M062XSDD_U[self.atoms[i]]
            self.properties["atomization"]=AE
            print(self.properties["energy"],self.properties["atomization"])
        elif (Level=='HF/6-31g*'):
            AE=self.properties["energy"]
            for i in range(0,self.atoms.shape[0]):
                AE=AE-HF631Gs_U[self.atoms[i]]
            self.properties["atomization"] =AE
            print (self.properties["energy"],self.properties["atomization"])
        else:
            raise Exception("Missing energy to calculate atomization... ")
        return
    def NAtoms(self):
        return self.atoms.shape[0]
    def AtomTypes(self):
        return np.unique(self.atoms)
    def Clean(self):
        pass
        return
    
    def __str__(self,wprop=False):
        lines =""
        natom = self.atoms.shape[0]
        if (wprop):
            lines = lines+(str(natom)+"\nComment: "+self.PropertyString()+"\n")
        else:
            lines = lines+(str(natom)+"\nComment: \n")
        for i in range (natom):
            atom_name =  self.atomnamelist[i]
            if (i<natom-1):
                lines = lines+(atom_name+"   "+str(self.coords[i][0])+ "  "+str(self.coords[i][1])+ "  "+str(self.coords[i][2])+"\n")
            else:
                lines = lines+(atom_name+"   "+str(self.coords[i][0])+ "  "+str(self.coords[i][1])+ "  "+str(self.coords[i][2]))
        return lines
    
    def __repr__(self):
        return self.__str__()
         