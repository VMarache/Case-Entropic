from tespy.networks import Network
from tespy.components import (
    Compressor,
    HeatExchanger,
    CycleCloser,
    Valve,
    Source,
    Sink,
)
from tespy.connections import Connection, Bus
#'R134a'
pump=Network(fluids=['NH3','water'],
             T_unit='degC',
             p_unit='bar',
             h_unit='kJ/kg',
             m_unit='kg/s',
             power_unit='kW')

cc=CycleCloser('Cycle Closer')
cp=Compressor('Compressor')
ev=HeatExchanger('Evaporator')
co=HeatExchanger('Condenser')
va=Valve('Expansion Valve')

src_in=Source('Heat Source In')
src_out=Sink('Heat Source Out')

snk_in=Source('Heat Sink in')
snk_out=Sink('Heat Sink Out')

c0=Connection(cc,'out1',ev,'in2',label='r0')
c1=Connection(ev,'out2',cp,'in1',label='r1')
c2=Connection(cp,'out1',co,'in1',label='r2')
c3=Connection(co,'out1',va,'in1',label='r3')
c4=Connection(va,'out1',cc,'in1',label='r4')

c_src_in=Connection(src_in,'out1',ev,'in1',label='src_in')
c_src_out=Connection(ev,'out1',src_out,'in1',label='src_out')

c_snk_in=Connection(snk_in,'out1',co,'in2',label='snk_in')
c_snk_out=Connection(co,'out2',snk_out,'in1',label='snk_out')

pump.add_conns(c0,c1,c2,c3,c4,c_snk_in,c_src_in,c_snk_out,c_src_out)

cp.set_attr(eta_s=0.85)
ev.set_attr(pr1=1, pr2=1)
co.set_attr(pr1=1, pr2=1,Q=-1012000)

# Evaporator refrigerant — fix evaporating state
c1.set_attr(fluid={'NH3':1}, T=0, x=1)
c3.set_attr(x=0)    

# Source — fixes evaporator duty to ~1000 kW
c_src_in.set_attr(fluid={'water':1}, T=40, p=2, m=7.97)
c_src_out.set_attr(T=10)

# Sink — fix both mass flow and outlet to enforce 1012 kW, 40→90°C
c_snk_in.set_attr(fluid={'water':1}, T=40, p=2)
c_snk_out.set_attr(T=90)

pump.solve(mode="design")
pump.print_results()

print(f"Q_ev          = {ev.Q.val/1000:.2f} kW")        # should be ~1000
print(f"Q_co          = {co.Q.val/1000:.2f} kW")        # should be ~-1012
print(f"T_src_in      = {c_src_in.T.val:.2f} °C")  # should be 40
print(f"T_src_out     = {c_src_out.T.val:.2f} °C") # should be 10
print(f"T_snk_in      = {c_snk_in.T.val:.2f} °C")  # should be 40
print(f"T_snk_out     = {c_snk_out.T.val:.2f} °C") # should be 90
print(f"eta_s         = {cp.eta_s.val:.2f}")        # should be 0.85
print(f"W_cp          = {cp.P.val/1000:.2f} kW")  # should be ~12 kW
print(f"ev.kA         = {ev.kA.val:.2f}")           # must not be nan
print(f"co.kA         = {co.kA.val:.2f}")           # must not be nan











