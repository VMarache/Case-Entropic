from tespy.networks import Network
from tespy.components import (
    Compressor,
    HeatExchanger,
    CycleCloser,
    Valve,
    Source,
    Sink,
)
from tespy.connections import Connection


class HeatPumpModel:
    def __init__(self):
        self.nw=Network()
        self.nw.units.set_defaults(temperature='degC',
                                   pressure="bar",
                                   enthalpy='kJ/kg',
                                   power='kW',
                                   mass_flow='kg/s')
        self.build_model()
    
    def build_model(self):
        self.cc=CycleCloser('Cycle Closer')
        self.cp=Compressor('Compressor')
        self.ev=HeatExchanger('Evaporator')
        self.co=HeatExchanger('Condenser')
        self.va=Valve('Expansion Valve')

        self.src_in=Source('Heat Source In')
        self.src_out=Sink('Heat Source Out')

        self.snk_in=Source('Heat Sink in')
        self.snk_out=Sink('Heat Sink Out')

        self.c0=Connection(self.cc,'out1',self.ev,'in2',label='r0')
        self.c1=Connection(self.ev,'out2',self.cp,'in1',label='r1')
        self.c2=Connection(self.cp,'out1',self.co,'in1',label='r2')
        self.c3=Connection(self.co,'out1',self.va,'in1',label='r3')
        self.c4=Connection(self.va,'out1',self.cc,'in1',label='r4')

        self.c_src_in=Connection(self.src_in,'out1',self.ev,'in1',label='src_in')
        self.c_src_out=Connection(self.ev,'out1',self.src_out,'in1',label='src_out')

        self.c_snk_in=Connection(self.snk_in,'out1',self.co,'in2',label='snk_in')
        self.c_snk_out=Connection(self.co,'out2',self.snk_out,'in1',label='snk_out')

        self.nw.add_conns(self.c0,self.c1,self.c2,self.c3,self.c4,self.c_snk_in,self.c_src_in,self.c_snk_out,self.c_src_out)

    def solve_design(self,eta_s,ref_fluid,ext_fluid,T_src_in,T_src_out,T_snk_in,T_snk_out,dt,P_src,P_snk):
        self.cp.set_attr(eta_s=eta_s)
        self.ev.set_attr(pr1=1, pr2=1)
        self.co.set_attr(pr1=1, pr2=1)

            # Evaporator refrigerant — fix evaporating state
        self.c1.set_attr(fluid={ref_fluid:1}, T=T_src_out-dt, x=1)
        self.c3.set_attr(T=T_snk_out+dt,x=0)       

        # Source — fixes evaporator duty to ~1000 kW
        self.c_src_in.set_attr(fluid={ext_fluid:1}, T=T_src_in, p=P_src, m=7.97)
        self.c_src_out.set_attr(T=T_src_out)

# Sink — fix both mass flow and outlet to enforce 1012 kW, 40→90°C
        self.c_snk_in.set_attr(fluid={ext_fluid:1}, T=T_snk_in, p=P_snk)
        self.c_snk_out.set_attr(T=T_snk_out)

        self.nw.solve(mode="design")
        self.nw.print_results()
        self.nw.save('design_case')

    def solve_offdesign(self,T_src_in_n,T_src_out_n,m_n,T_snk_in_n,T_snk_out_n,Q_co_n):
        self.c_src_in.set_attr(T=T_src_in_n,m=m_n)
        self.c_src_out.set_attr(T=T_src_out_n)

        self.c_snk_in.set_attr(T=T_snk_in_n)
        self.c_snk_out.set_attr(T=T_snk_out_n)

        self.co.set_attr(Q=None)
        self.nw.solve('offdesign', design_path='design_case')


model=HeatPumpModel()
model.solve_design(0.85,'NH3','water',40,10,40,90,10,2,2)

print(f"Q_ev          = {model.ev.Q.val/1000:.2f} kW")        
print(f"Q_co          = {model.co.Q.val/1000:.2f} kW")     
print(f"T_src_in      = {model.c_src_in.T.val:.2f} °C") 
print(f"T_src_out     = {model.c_src_out.T.val:.2f} °C")
print(f"T_snk_in      = {model.c_snk_in.T.val:.2f} °C") 
print(f"T_snk_out     = {model.c_snk_out.T.val:.2f} °C") 
print(f"eta_s         = {model.cp.eta_s.val:.2f}")       
print(f"W_cp          = {model.cp.P.val:.2f} kW")  
print(f"ev.kA         = {model.ev.kA.val:.2f}")          
print(f"co.kA         = {model.co.kA.val:.2f}") 