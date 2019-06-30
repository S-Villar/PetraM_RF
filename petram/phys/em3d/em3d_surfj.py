'''
   Surface Current Boundary Condition

   On external surface    n \times B = J_surf
   On internal surface    n \times (B1 - B2) = J_surf (not tested)

   (note)
    In MKSA,  1/mu curl E = -dB/dt 1/mu= i omega B / mu .
      n \times 1/mu curl E = -dB/dt 1/mu= i omega B / mu = i omega /mu J_surf
    
 
    Therefore, surface integral 
        \int W \dot (n \times 1/mu curl E) d\Omega
    becomes
         \int W \dot (i omega J_surf) d\Omega

    and VectorFEDomainLFIntegrator can be used.


   CopyRight (c) 2016-  S. Shiraiwa
''' 
import numpy as np

from petram.phys.phys_model  import Phys, VectorPhysCoefficient
from petram.phys.em3d.em3d_base import EM3D_Bdry, EM3D_Domain

import petram.debug as debug
dprint1, dprint2, dprint3 = debug.init_dprints('EM3D_SurfJ')

from petram.mfem_config import use_parallel
if use_parallel:
   import mfem.par as mfem
else:
   import mfem.ser as mfem

from petram.phys.vtable import VtableElement, Vtable      
data =  (('surfJ', VtableElement('surfJ', type='complex',
                             guilabel = 'Surface J',
                             suffix =('x', 'y', 'z'),
                             default = [0,0,0],
                             tip = "surface current" )),)
   
class Jsurf(VectorPhysCoefficient):
   def __init__(self, *args, **kwargs):
       omega = kwargs.pop('omega', 1.0)
       self.mur = kwargs.pop('mur', 1.0)
       from .em3d_const import mu0, epsilon0
       self.fac = -1j*omega
       super(Jsurf, self).__init__(*args, **kwargs)

   def EvalValue(self, x):
       from .em3d_const import mu0, epsilon0      
       v = super(Jsurf, self).EvalValue(x)
       v = self.fac * v
       if self.real:  return v.real
       else: return v.imag


class EM3D_SurfJ(EM3D_Bdry):
    is_essential = False
    vt  = Vtable(data)

    def has_lf_contribution(self, kfes = 0):
        if kfes != 0: return False
        return True
    
    def add_lf_contribution(self, engine, b, real = True, kfes = 0):
        if kfes != 0: return 
        if real:       
            dprint1("Add LF contribution(real)" + str(self._sel_index))
        else:
            dprint1("Add LF contribution(imag)" + str(self._sel_index))

        freq, omega = self.get_root_phys().get_freq_omega()        
        f_name = self.vt.make_value_or_expression(self)
        
        coeff1 = Jsurf(3, f_name[0],  self.get_root_phys().ind_vars,
                            self._local_ns, self._global_ns,
                            real = real, omega = omega,)
        
        self.add_integrator(engine, 'surfJ', coeff1,
                            b.AddBoundaryIntegrator,
                            mfem.VectorFEDomainLFIntegrator)
        '''
        coeff1 = self.restrict_coeff(coeff1, engine, vec = True)
        b.AddBoundaryIntegrator(mfem.VectorFEDomainLFIntegrator(coeff1))
        '''

