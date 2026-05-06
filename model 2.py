import pandas as pd 
import matplotlib.pyplot as plt
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
        """Creates the network"""
        self.nw=Network()
        self.nw.units.set_defaults(temperature='degC',
                                   pressure="bar",
                                   enthalpy='kJ/kg',
                                   power='kW',
                                   mass_flow='kg/s')
        self.build_model()
    
    def build_model(self):
        """Function that builds the framework"""

        # Components
        self.cc=CycleCloser('Cycle Closer')
        self.cp=Compressor('Compressor')
        self.ev=HeatExchanger('Evaporator')
        self.co=HeatExchanger('Condenser')
        self.va=Valve('Expansion Valve')

        self.src_in=Source('Heat Source In')
        self.src_out=Sink('Heat Source Out')

        self.snk_in=Source('Heat Sink in')
        self.snk_out=Sink('Heat Sink Out')

        # Connections
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
        """Function  that design the model based on given parameters
        -----------------
        Parameters
        -----------------
        eta_s: float
           compressor efficiency
        ref_fluid:str
            refrigerant fluid
        ext_fluid:str
            fluid in the heat source and sink
        T_src_in: float
            Temperature at the inflow of the heat source
        T_src_out: float
            Temperature at the outflow of the heat source
        T_snk_in: Float
            Temperature at the inflow of the heat sink
        T_snk_out: Float
            Temperature at the outflow of the heat sink
        dt: Float
            Difference in temp between the refrigerant and the other fluid at the outflow of the evaporator/condenser
        P_src:
            Pressure at the heat source
        P_snk: Float
            Pressure at the heat sink 
        """
        # Conditions for the different components
        self.cp.set_attr(eta_s=eta_s,design=['eta_s'],offdesign=['eta_s'])
        self.ev.set_attr(pr1=1, pr2=1,design=['pr1','pr2'],offdesign=['zeta1', 'zeta2', 'kA_char1', 'kA_char2'])
        self.co.set_attr(pr1=1, pr2=1,design=['pr1','pr2'],offdesign=['zeta1', 'zeta2', 'kA_char1', 'kA_char2'])
        self.va.set_attr(design=['pr'],offdesign=['zeta'])

        # Conditions for the refrigerant flow
        self.c1.set_attr(fluid={ref_fluid:1}, T=T_src_out-dt, x=1)
        self.c3.set_attr(T=T_snk_out+dt,x=0)       

        # Heat source conditions
        self.c_src_in.set_attr(fluid={ext_fluid:1}, T=T_src_in, p=P_src, m=7.97)
        self.c_src_out.set_attr(T=T_src_out)

        #Heat sink conditions
        self.c_snk_in.set_attr(fluid={ext_fluid:1}, T=T_snk_in, p=P_snk)
        self.c_snk_out.set_attr(T=T_snk_out)

        # Solving
        self.nw.solve(mode="design")
        self.nw.print_results()
        self.nw.save('design_case')

        # Printing parameters to check
        print(f"Q_ev      = {abs(self.ev.Q.val_SI)/1000:.2f} kW")
        print(f"Q_co      = {abs(self.co.Q.val_SI)/1000:.2f} kW")
        print(f"T_snk_out = {self.c_snk_out.T.val:.2f} °C")
        print(f"m_snk     = {self.c_snk_in.m.val:.3f} kg/s")
        print(f"W_cp      = {self.cp.P.val:.2f} kW")
        print(f"COP       = {abs(self.co.Q.val_SI)/self.cp.P.val_SI:.2f}")
        print(f"ev.kA     = {self.ev.kA.val:.2f}")
        print(f"co.kA     = {self.co.kA.val:.2f}")



    def solve_offdesign_T_src(self,T_src_in_n,T_src_out_n,m_n,T_snk_in_n,T_snk_out_n):
        """" Function to solve off design based on different conditions for heat source and sink
        ------------
        Parameters
        ------------
        T_src_in_n: float
            New temperature at the inflow of the heat source
        T_src_out_n: float
            New temperature at the outflow of the heat source
        m_n: Float
            New mass flow of the heat source
        T_snk_in_n: Float
            New temperature at the inflow of the heat sink
        T_snk_out_n: Float
            New temperature at the outflow of the heat sink
        """
        # Setting new conditions for heat source
        self.c_src_in.set_attr(T=T_src_in_n, m=m_n)
        self.c_src_out.set_attr(T=T_src_out_n)

        # Setting new conditions for heat sink
        self.c_snk_in.set_attr(T=T_snk_in_n,m=None)
        self.c_snk_out.set_attr(T=T_snk_out_n)

        # Resetting conditions for refrigerant flow
        self.c1.set_attr(T=None) 
        self.c3.set_attr(T=T_snk_out_n+10)
        
        self.nw.solve('offdesign', design_path='design_case')

    def visualize(self,time,T_src_in,T_src_out,m_src,T_snk_in,T_snk_out):
        """" Function to visualize the solved off design with different conditions for heat source and sink
        ------------
        Parameters
        ------------
        time: pandas.Series
            Serie of datetime for the different conditions
        T_src_in: pandas.Series
            Serie of new temperatures at the inflow of the heat source
        T_src_out: pandas.Series
            Serie of new temperatures at the outflow of the heat source
        m_src: pandas.Series
            Serie of new mass flow of the heat source
        T_snk_in: pandas.Series
            Serie of new temperatures at the inflow of the heat sink
        T_snk_out: pandas.Series
            Serie of new temperatures at the outflow of the heat sink
        """

        # Setting empty list for values
        COPs_T=[]
        P_comp_T=[]
        kA_ev_T=[]
        kA_co_T=[]
        mass_co=[]

        # Looping solving for the different conditions and storing results
        for i in range(len(T_src_in)):
            if T_src_in[i]<=T_src_out[i]:
                COPs_T.append(0)
                P_comp_T.append(0)
                kA_ev_T.append(0)
                kA_co_T.append(0)
                mass_co.append(0)
            else:
                self.solve_offdesign_T_src(T_src_in[i],T_src_out[i],m_src[i],T_snk_in[i],T_snk_out[i])
                COPs_T.append(abs(self.co.Q.val_SI)/model.cp.P.val_SI)
                P_comp_T.append(self.cp.P.val)
                kA_ev_T.append(abs(self.ev.Q.val_SI)/1000)
                kA_co_T.append(abs(self.co.Q.val_SI)/1000)
                mass_co.append(self.c_snk_in.m.val)
       
        # Plotting the results       
        plt.figure(1)
        plt.plot(time,COPs_T)
        plt.xlabel('Time')
        plt.ylabel('COP')
        plt.title('COP values ')
        plt.show()

        plt.figure(2)
        plt.plot(time,P_comp_T)
        plt.xlabel('Time')
        plt.ylabel('P (kW)')
        plt.title('Power consumption of the compressor ')
        plt.show()

        plt.figure(3)
        plt.plot(time,kA_ev_T)
        plt.xlabel('Time')
        plt.ylabel('kA')
        plt.title('Heat transfer rates in the evaporator ')
        plt.show()

        plt.figure(4)
        plt.plot(time,kA_co_T)
        plt.xlabel('Time')
        plt.ylabel('kA')
        plt.title('Heat transfer rates in the condenser ')
        plt.show()

        plt.figure(5)
        plt.plot(time,mass_co)
        plt.xlabel('Time')
        plt.ylabel('Flow (kg/s)')
        plt.title('Mass flow in the condenser')
        plt.show()


# Extracting the data from excel
data=pd.read_excel('HP_case_data.xlsx',sheet_name=None)
df_src = data['Heat source']   # replace with your actual sheet name
df_snk = data['Heat sink']
T_src_in=df_src['T_in[degC']
T_src_out=df_src['T_out[degC]']
m_src=df_src['flow[kg/s]']
T_snk_in=df_snk['T_in[degC']
T_snk_out=df_snk['T_out[degC]']

# transforming tim estamps in data to datetime
df_src['end measurement']=pd.to_datetime(df_src['end measurement'])

# Running the model
model=HeatPumpModel()
model.solve_design(0.85,'NH3','water',40,10,40,90,10,2,2)
model.visualize(df_src['end measurement'],T_src_in,T_src_out,m_src,T_snk_in,T_snk_out)




























