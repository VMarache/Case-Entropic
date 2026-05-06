# Case Entropic — Heat Pump Model
 
A Python-based simulation model for a vapour-compression heat pump, built with [TESPy](https://tespy.readthedocs.io/). The model supports both design-point solving and off-design analysis over time-series data, with built-in visualisation of key performance indicators.
 
---
 
## Overview
 
The model simulates a heat pump cycle consisting of:
- **Compressor**
- **Condenser** (heat sink side)
- **Expansion Valve**
- **Evaporator** (heat source side)
- **Cycle Closer**
It reads real-world operating data from an Excel file and evaluates performance across varying conditions.
 
---
 
## Requirements
 
- Python 3.8+
- [TESPy](https://tespy.readthedocs.io/) — `pip install tespy`
- pandas — `pip install pandas`
- matplotlib — `pip install matplotlib`
- openpyxl — `pip install openpyxl` (for reading `.xlsx` files)
---
 
## Input Data
 
The model expects an Excel file named `HP_case_data.xlsx` in the working directory, with two sheets:
 
| Sheet | Columns |
|---|---|
| `Heat source` | `end measurement`, `T_in[degC`, `T_out[degC]`, `flow[kg/s]` |
| `Heat sink` | `T_in[degC`, `T_out[degC]`, `Energy[kWh]` |
 
---
 
## Usage
 
### 1. Design Point
 
Solves the heat pump at a fixed operating point:
 
```python
model = HeatPumpModel()
model.solve_design(
    eta_s=0.85,        # Compressor isentropic efficiency
    ref_fluid='NH3',   # Working fluid (refrigerant)
    ext_fluid='water', # Heat source/sink fluid
    T_src_in=40,       # Heat source inlet temperature [°C]
    T_src_out=10,      # Heat source outlet temperature [°C]
    T_snk_in=40,       # Heat sink inlet temperature [°C]
    T_snk_out=90,      # Heat sink outlet temperature [°C]
    dt=10,             # Pinch point temperature difference [K]
    P_src=2,           # Heat source pressure [bar]
    P_snk=2            # Heat sink pressure [bar]
)
```
 
Prints evaporator/condenser heat loads, compressor power, COP, and heat transfer coefficients (kA).
 
---
 
### 2. Off-Design — Variable Heat Source
 
Solves off-design across time-series data with varying heat source temperatures and mass flow:
 
```python
model.visualize_T_src(time, T_src_in, T_src_out, m_src, T_snk_in, T_snk_out)
```
 
Time steps where `T_src_in <= T_src_out` are skipped and set to zero in the results.
 
---
 
### 3. Off-Design — Variable Heat Sink Load
 
Solves off-design across time-series data driven by varying heat sink demand. Mass flow in the sink is derived from the heat load `Q_snk` and fluid heat capacity `Cp_snk`:
 
```python
model.visualize_Q_snk(time, Q_snk, T_snk_in, T_snk_out, Cp_snk=4.18)
```
 
Time steps where `Q_snk = 0` are skipped and set to zero in the results.
 
---
 
## Outputs
 
Both visualisation methods produce five plots:
 
1. **COP** over time
2. **Compressor power** (kW) over time
3. **Evaporator heat transfer rate** (kW) over time
4. **Condenser heat transfer rate** (kW) over time
5. **Mass flow** in the condenser/evaporator (kg/s) over time

A `design_case/` folder is also saved after the design solve, used as the reference point for all off-design calculations.
 
---
 
## Project Structure
 
```
├── HP_model.py          # Main model file
├── HP_case_data.xlsx    # Input data (not included in repo)
├── design_case/         # Auto-generated after design solve
└── README.md
```
 
---
 
## Notes
 
- The `solve_offdesign_Q_snk` method calculates sink mass flow as `m = Q / (Cp * ΔT)`, so `T_snk_in` and `T_snk_out` must differ.
- The model uses `NH3` (ammonia) as the default refrigerant and `water` as the heat transfer fluid, but these can be changed in `solve_design()`.
- The heat source mass flow is freed (`m=None`) in the Q-sink off-design mode, allowing the solver to find it freely.
