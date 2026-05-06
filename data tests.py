from tespy.networks import Network
from tespy.components import Compressor, HeatExchanger, CycleCloser, Valve, Source, Sink
from tespy.connections import Connection


class SimpleHeatPump:

    def __init__(self):

        self.nw = Network(
            fluids=["water", "R134a"],
            p_unit="bar",
            T_unit="C",
            h_unit="kJ/kg"
        )

        # Components
        self.cc = CycleCloser("cycle closer")
        self.cp = Compressor("compressor")
        self.ev = HeatExchanger("evaporator")
        self.co = HeatExchanger("condenser")
        self.va = Valve("valve")

        self.src = Source("heat source")
        self.snk = Sink("heat sink")

        # Refrigerant cycle
        self.c0 = Connection(self.cc, "out1", self.ev, "in2")
        self.c1 = Connection(self.ev, "out2", self.cp, "in1")
        self.c2 = Connection(self.cp, "out1", self.co, "in1")
        self.c3 = Connection(self.co, "out1", self.va, "in1")
        self.c4 = Connection(self.va, "out1", self.cc, "in1")

        # External circuits
        self.cs_in = Connection(self.src, "out1", self.ev, "in1")
        self.cs_out = Connection(self.ev, "out1", self.src, "in1")

        self.ck_in = Connection(self.snk, "out1", self.co, "in2")
        self.ck_out = Connection(self.co, "out2", self.snk, "in1")

        self.nw.add_conns(
            self.c0, self.c1, self.c2, self.c3, self.c4,
            self.cs_in, self.cs_out,
            self.ck_in, self.ck_out
        )

        self.build_design()

    # ---------------- DESIGN ----------------
    def build_design(self):

        # Working fluid
        self.c1.set_attr(fluid={"R134a": 1}, x=1)
        self.c3.set_attr(x=0)

        # Compressor
        self.cp.set_attr(eta_s=0.75)

        # Heat exchangers (design UA behaviour)
        self.ev.set_attr(pr1=0.98, pr2=0.98)
        self.co.set_attr(pr1=0.98, pr2=0.98)

        self.va.set_attr(pr=1)

        # External conditions
        self.cs_in.set_attr(T=5, m=1, fluid={"water": 1})
        self.ck_in.set_attr(T=35, fluid={"water": 1})

        # Refrigerant boundary guesses (important for convergence)
        self.c1.set_attr(T=0)
        self.c3.set_attr(T=40)

        # Solve design
        self.nw.solve("design")
        self.nw.save("design_case")

        print("\n--- DESIGN RESULTS ---")
        print(f"Q_ev = {self.ev.Q.val_SI/1000:.2f} kW")
        print(f"Q_co = {self.co.Q.val_SI/1000:.2f} kW")
        print(f"COP  = {abs(self.co.Q.val_SI)/self.cp.P.val_SI:.2f}")

    # ---------------- OFF-DESIGN ----------------
    def solve_offdesign(self, T_src_in, m_src, T_sink_in):

        # ONLY boundary conditions
        self.cs_in.set_attr(T=T_src_in, m=m_src)
        self.ck_in.set_attr(T=T_sink_in)

        # FREE heat exchangers (critical!)
        self.ev.set_attr(Q=None)
        self.co.set_attr(Q=None)

        # Solve offdesign
        self.nw.solve("offdesign", design_path="design_case")

        print("\n--- OFF-DESIGN RESULTS ---")
        print(f"T_sink_out = {self.ck_out.T.val:.2f} °C")
        print(f"Q_ev       = {self.ev.Q.val_SI/1000:.2f} kW")
        print(f"Q_co       = {self.co.Q.val_SI/1000:.2f} kW")
        print(f"COP        = {abs(self.co.Q.val_SI)/self.cp.P.val_SI:.2f}")

model=SimpleHeatPump()
model.solve_offdesign(55,2,60)