import numpy as np
from utils.depend import *
from utils.restart import *
from utils import units



class Atom(dobject):
   """Represent an atom, with position, velocity, mass and related properties."""
            
   def __init__(self, system, index, label="X"):
      self.name=label
      dset(self,"p",system.p[3*index:3*index+3])
      dset(self,"q",system.q[3*index:3*index+3])
      dset(self,"m",system.m[index:index+1])
      dset(self,"m3",system.m3[3*index:3*index+3])
      
      dset(self,"kin",depend_value(name="kin", deps=depend_func(func=self.get_kin, dependencies=[depget(self,"p"),depget(self,"m3")]) ))
      dset(self,"kstress",depend_value(name="kstress", 
                         deps=depend_func(func=self.get_kstress, dependencies=[depget(self,"p"),depget(self,"m")]) ))

   def get_kin(self):
      return np.dot(self.p,self.p)/(2.0*self.m)

   def get_kstress(self):
      """Calculates the contribution of the atom to the kinetic stress tensor"""
      p=self.p.view(ndarray)
      ks = numpy.zeros((3,3),float)
      for i in range(3):
         for j in range(i,3):
            ks[i,j] = p[i]*p[j]            
      return ks/self.m

class RestartAtoms(Restart):
   fields={ "natoms" : (RestartValue, (int,None)), "q" : (RestartArray,(float,np.zeros(0))),  "p" : (RestartArray,(float,np.zeros(0))),
            "m" : (RestartArray,(float, np.zeros(0))),  "names" : (RestartArray,(str,np.zeros(0, str))),
            "filename" : (RestartValue,(str, "")) }
       
   def __init__(self, atoms=None, filename=""):
      super(RestartAtoms,self).__init__()
      if not atoms is None: self.store(atoms, filename="")
                       
   def store(self, atoms, filename=""):
      self.natoms.store(atoms.natoms)
      self.q.store(depstrip(atoms.q))
      self.p.store(depstrip(atoms.p))
      self.m.store(depstrip(atoms.m))
      self.names.store(np.array([a.name for a in atoms]))
      self.filename.store(filename)
      
   def fetch(self):
      atoms=Atoms(self.natoms.fetch())
      atoms.q=self.q.fetch()
      atoms.p=self.p.fetch()      
      atoms.m=self.m.fetch()   
      i=0
      for n in self.names.fetch(): 
         atoms[i].name=n; i+=1
      return atoms
   
   def check(self): 
      # if required get data from file and/or initialize
      pass
         
class Atoms(dobject):
   """Represents a simulation cell. Includes the cell parameters, 
      the atoms and the like."""   

   def __init__(self, natoms):
      self.natoms=natoms
      dset(self,"q",depend_array(name="q",value=np.zeros(3*natoms, float)) ) 
      dset(self,"p",depend_array(name="p",value=np.zeros(3*natoms, float)) )
      dset(self,"px",self.p[0:3*natoms:3]);       dset(self,"py",self.p[1:3*natoms:3]);      dset(self,"pz",self.p[2:3*natoms:3])
      dset(self,"qx",self.q[0:3*natoms:3]);       dset(self,"qy",self.q[1:3*natoms:3]);      dset(self,"qz",self.q[2:3*natoms:3])      
      
      dset(self,"m",depend_array(name="m",value=np.zeros(natoms, float)) )

      #interface to get a 3*n-sized array with masses      
      dset(self,"m3",depend_array(name="m3",value=np.zeros(3*natoms, float),deps=depend_func(func=self.mtom3, dependencies=[depget(self,"m")])))
      
      self._alist=[ Atom(self, i) for i in range(natoms) ]

      dset(self,"M",depend_value(name="M",deps=depend_func(func=self.get_msum,dependencies=[depget(self,"m")])) )      
      dset(self,"kin",depend_value(name="kin",deps=depend_func(func=self.get_kin,dependencies=[depget(self,"p"),depget(self,"m3")])) )
      dset(self,"kstress",depend_value(name="kstress",deps=depend_func(func=self.get_kstress,dependencies=[depget(self,"p"),depget(self,"m")])) )
   
   def __len__(self): return self.natoms

   def get_msum(self): return self.m.sum()
   
   def mtom3(self): m3=np.zeros(3*self.natoms,float); m3[0:3*self.natoms:3]=self.m; m3[1:3*self.natoms:3]=m3[0:3*self.natoms:3]; m3[2:3*self.natoms:3]=m3[0:3*self.natoms:3]; return m3
   
   def __getitem__(self,index):
      return self._alist[index]

   def __setitem__(self,index,value):
      self._alist[index].p=value.p
      self._alist[index].q=value.q 
      self._alist[index].m=value.m
                  
   def get_kin(self):
      """Calculates the total kinetic energy of the system,
      by summing the atomic contributions"""
      return 0.5*np.dot(self.p,self.p/self.m3)
      
   def get_kstress(self):
      """Calculates the contribution of the atom to the kinetic stress tensor"""
      p=self.p.view(np.ndarray)
      ks = numpy.zeros((3,3),float)
      ks[0,0]=np.dot(self.px,self.px/self.m)
      ks[1,1]=np.dot(self.py,self.py/self.m)
      ks[2,2]=np.dot(self.pz,self.pz/self.m)
      ks[0,1]=np.dot(self.px,self.py/self.m)
      ks[0,2]=np.dot(self.px,self.pz/self.m)
      ks[1,2]=np.dot(self.py,self.pz/self.m)                        
#      for i in range(3):
#         for j in range(i,3):
#            ks[i,j] = np.dot(p[i:self.natoms*3:3], p[j:self.natoms*3:3]/self.m)
      return ks
      
