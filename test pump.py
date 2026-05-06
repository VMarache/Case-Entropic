"""
Heat Pump Model — Fully Specified Operating Point
==================================================
Refrigerant cycle with real secondary fluid streams on both sides.

  Heat source (water): 40 °C → 10 °C,  Q_evap = 1000 kW
  Heat sink  (water): 40 °C → 90 °C,  Q_cond = 1012 kW
  Compressor isentropic efficiency: η_s = 0.85

The 12 kW difference is the compressor shaft power:
    W_cp = Q_cond - Q_evap = 1012 - 1000 = 12 kW
    COP  = Q_cond / W_cp   = 1012 / 12  ≈ 84.3  (ideal upper bound check)

Cycle state points
------------------
    [1] Evaporator outlet  — superheated vapour  → Compressor inlet
    [2] Compressor outlet  — hot high-p vapour   → Condenser inlet
    [3] Condenser outlet   — subcooled liquid     → Expansion valve inlet
    [4] Expansion valve outlet — wet mixture      → Evaporator inlet

Secondary streams
-----------------
    source_in  / source_out  : heat-source water (evaporator shell side)
    sink_in    / sink_out    : heat-sink   water (condenser shell side)
"""

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


# ──────────────────────────────────────────────────────────────────────
# User-adjustable parameters
# ──────────────────────────────────────────────────────────────────────
FLUID_REF   = "R410A"       # refrigerant (any CoolProp name)
FLUID_SEC   = "Water"       # secondary fluid (both sides)

# Compressor
ETA_S       = 0.85          # isentropic efficiency [-]

# Heat source side (evaporator secondary)
T_SRC_IN    = 40.0          # source inlet  temperature [°C]
T_SRC_OUT   = 10.0          # source outlet temperature [°C]
Q_EVAP      = 1000e3        # evaporator heat duty [W]  (+ve = absorbed by ref.)

# Heat sink side (condenser secondary)
T_SNK_IN    = 40.0          # sink inlet  temperature [°C]
T_SNK_OUT   = 90.0          # sink outlet temperature [°C]
Q_COND      = 1012e3        # condenser heat duty [W]  (rejected to sink)

# Approach temperatures (min ΔT between ref. and secondary)
DT_EVAP     = 5.0           # approach at evaporator [K]
DT_COND     = 5.0           # approach at condenser  [K]
SUPERHEAT   = 5.0           # superheat at compressor inlet [K]
SUBCOOL     = 5.0           # subcooling at condenser outlet [K]

# Derived saturation temperatures
T_EVAP_SAT  = T_SRC_OUT + DT_EVAP      # refrigerant evap. sat. temp [°C]
T_COND_SAT  = T_SNK_OUT - DT_COND      # refrigerant cond. sat. temp [°C]

# ──────────────────────────────────────────────────────────────────────


def build_heat_pump() -> Network:
    """Build, solve, and report the heat pump model."""

    print("=" * 60)
    print("  HEAT PUMP MODEL — TESPY")
    print("=" * 60)
    print(f"  Refrigerant          : {FLUID_REF}")
    print(f"  Compressor η_s       : {ETA_S}")
    print(f"  Heat source          : {T_SRC_IN} → {T_SRC_OUT} °C  |  Q = {Q_EVAP/1e3:.0f} kW")
    print(f"  Heat sink            : {T_SNK_IN} → {T_SNK_OUT} °C  |  Q = {Q_COND/1e3:.0f} kW")
    print(f"  Ref. evap. sat. temp : {T_EVAP_SAT:.1f} °C  (approach = {DT_EVAP} K)")
    print(f"  Ref. cond. sat. temp : {T_COND_SAT:.1f} °C  (approach = {DT_COND} K)")
    print("=" * 60 + "\n")

    # ── 1. Network ────────────────────────────────────────────────────
    nw = Network(
        fluids=[FLUID_REF, FLUID_SEC],
        T_unit="C",
        p_unit="bar",
        h_unit="kJ / kg",
        m_unit="kg / s",
    )

    # ── 2. Components ─────────────────────────────────────────────────
    cc   = CycleCloser("Cycle Closer")
    cp   = Compressor("Compressor")
    cond = HeatExchanger("Condenser")
    evap = HeatExchanger("Evaporator")
    val  = Valve("Expansion Valve")

    # Secondary-side sources & sinks
    src_in_comp  = Source("Heat Source Inlet")
    src_out_comp = Sink("Heat Source Outlet")
    snk_in_comp  = Source("Heat Sink Inlet")
    snk_out_comp = Sink("Heat Sink Outlet")

    # ── 3. Connections ────────────────────────────────────────────────
    # Refrigerant loop
    c_cc_ev  = Connection(cc,   "out1", evap, "in2",  label="ref_0")  # before evap
    c_ev_cp  = Connection(evap, "out2", cp,   "in1",  label="ref_1")  # evap → comp
    c_cp_cd  = Connection(cp,   "out1", cond, "in1",  label="ref_2")  # comp → cond
    c_cd_val = Connection(cond, "out1", val,  "in1",  label="ref_3")  # cond → valve
    c_val_cc = Connection(val,  "out1", cc,   "in1",  label="ref_4")  # valve → cc

    # Heat source (evaporator shell side — hot water gives heat to ref.)
    c_src_in  = Connection(src_in_comp,  "out1", evap, "in1",  label="src_in")
    c_src_out = Connection(evap,         "out1", src_out_comp, "in1", label="src_out")

    # Heat sink (condenser shell side — cold water receives heat from ref.)
    c_snk_in  = Connection(snk_in_comp,  "out1", cond, "in2",  label="snk_in")
    c_snk_out = Connection(cond,         "out2", snk_out_comp, "in1", label="snk_out")

    nw.add_conns(
        c_cc_ev, c_ev_cp, c_cp_cd, c_cd_val, c_val_cc,
        c_src_in, c_src_out,
        c_snk_in, c_snk_out,
    )

    # ── 4. Component parameters ───────────────────────────────────────
    cp.set_attr(eta_s=ETA_S)

    # Heat exchangers: no pressure drop on either side
    evap.set_attr(pr1=1, pr2=1, Q=Q_EVAP)
    cond.set_attr(pr1=1, pr2=1, Q=-Q_COND)

    # ── 5. Connection parameters — refrigerant ────────────────────────
    # State [1]: superheated vapour leaving evaporator
    c_ev_cp.set_attr(
        fluid={FLUID_REF: 1},
        T=T_EVAP_SAT + SUPERHEAT   # sat. temp + superheat                      
    )

    # State [3]: subcooled liquid leaving condenser
    c_cd_val.set_attr(
        T=T_COND_SAT - SUBCOOL     # sat. temp - subcooling
    )

    # Fix saturation pressures via temperature specification at cycle closer
    c_cc_ev.set_attr(T=T_EVAP_SAT)   # sat. liquid into evaporator

    # State [2]: compressor outlet temperature — leave free (solved by η_s)

    # ── 6. Connection parameters — secondary fluids ───────────────────
    # Heat source water
    c_src_in.set_attr(
        fluid={FLUID_SEC: 1},
        T=T_SRC_IN,
        p=3,          # [bar] — arbitrary, above saturation
    )
    c_src_out.set_attr(T=T_SRC_OUT)

    # Heat sink water
    c_snk_in.set_attr(
        fluid={FLUID_SEC: 1},
        T=T_SNK_IN,
        p=6,          # [bar] — above saturation at 90 °C
    )
    c_snk_out.set_attr(T=T_SNK_OUT)

    # ── 7. Power bus ──────────────────────────────────────────────────
    power_bus = Bus("Compressor Power")
    power_bus.add_comps({"comp": cp, "base": "bus"})
    nw.add_busses(power_bus)

    # ── 8. Solve ──────────────────────────────────────────────────────
    nw.solve(mode="design")
    nw.print_results()

    # ── 9. KPIs ───────────────────────────────────────────────────────
    W_cp  = abs(cp.P.val)
    Q_h   = abs(cond.Q.val)
    Q_l   = abs(evap.Q.val)
    COP   = Q_h / W_cp

    T_cond_K = T_COND_SAT + 273.15
    T_evap_K = T_EVAP_SAT + 273.15
    COP_carnot = T_cond_K / (T_cond_K - T_evap_K)
    eta_ex = COP / COP_carnot

    m_ref  = c_ev_cp.m.val
    m_src  = c_src_in.m.val
    m_snk  = c_snk_in.m.val

    T_ref_evap_in  = c_cc_ev.T.val
    T_ref_evap_out = c_ev_cp.T.val
    T_ref_cond_in  = c_cp_cd.T.val
    T_ref_cond_out = c_cd_val.T.val
    p_low  = c_cc_ev.p.val
    p_high = c_cp_cd.p.val
    pr_cp  = p_high / p_low

    print("\n" + "=" * 60)
    print("  PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"\n  {'--- Thermodynamic ---'}")
    print(f"  Evap. pressure       : {p_low:.2f}  bar")
    print(f"  Cond. pressure       : {p_high:.2f}  bar")
    print(f"  Pressure ratio       : {pr_cp:.2f}")
    print(f"  Ref. temp @ evap in  : {T_ref_evap_in:.1f}  °C  (sat. liquid)")
    print(f"  Ref. temp @ evap out : {T_ref_evap_out:.1f}  °C  (superheated)")
    print(f"  Ref. temp @ cond in  : {T_ref_cond_in:.1f}  °C  (hot vapour)")
    print(f"  Ref. temp @ cond out : {T_ref_cond_out:.1f}  °C  (subcooled)")
    print(f"\n  {'--- Heat & Power ---'}")
    print(f"  Q_evaporator (Q_L)   : {Q_l/1e3:.2f}  kW")
    print(f"  Q_condenser  (Q_H)   : {Q_h/1e3:.2f}  kW")
    print(f"  W_compressor         : {W_cp/1e3:.2f}  kW")
    print(f"  Energy balance check : Q_L + W = {(Q_l+W_cp)/1e3:.2f} kW  (≈ Q_H?)")
    print(f"\n  {'--- Mass Flows ---'}")
    print(f"  Refrigerant ṁ        : {m_ref:.3f}  kg/s")
    print(f"  Source water ṁ       : {m_src:.3f}  kg/s")
    print(f"  Sink water ṁ         : {m_snk:.3f}  kg/s")
    print(f"\n  {'--- COP ---'}")
    print(f"  COP (heating)        : {COP:.3f}")
    print(f"  COP Carnot (ideal)   : {COP_carnot:.3f}")
    print(f"  Exergetic efficiency : {eta_ex*100:.1f}  %")
    print("=" * 60)

    return nw


if __name__ == "__main__":
    nw = build_heat_pump()