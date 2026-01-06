# WSN Routing Simulation Suite

This repository contains a comprehensive suite for simulating and optimizing Wireless Sensor Network (WSN) routing protocols with support for LEACH, APTEEN, and JSO-based algorithms.

## Project Architecture

### Core Modules

#### `router/` - Routing Protocol Implementation
- **`node.py`**: Node class with energy models and communication methods
- **`router.py`**: Base routing protocol interface
- **`routing.py`**: Graph algorithms (Prim's MST, etc.)
- **`common.py`**: Shared utilities for routing protocols
- **`apteen.py`**: APTEEN protocol implementation
- **`jso_route.py`**: JSO-optimized routing (JSOGreedy, JSOPrim, JSOKalman)
- **`leach/`**: LEACH protocol variants
  - `leach.py`: Standard LEACH protocol
  - `leach_pso.py`: PSO-optimized LEACH
  - `hierarchical.py`: Hierarchical clustering

#### `optimizer/` - Metaheuristic Optimization
- **`optimizer.py`**: JSO (Jellyfish Search Optimizer) and PSO implementations
- **`initializer.py`**: Logistic chaos map for population initialization
- **`common.py`**: Shared optimization utilities

### Utility Scripts

#### `distribution.py` - Network Topology Generation
Generates various sensor node distributions:
- **`uniform_in_square()`**: Uniform distribution in square area
- **`uniform_in_circle()`**: Uniform distribution in circular area
- **`power_line_naive()`**: Power line topology with relay nodes
- **`simple_loader()`**: Load predefined node positions

#### `kalman_energy_estimation.py` - Energy Prediction
Demonstrates Kalman filter-based energy prediction for WSN nodes. Uses historical energy data to estimate future energy consumption patterns.

## Scripts Overview

### 1. `test_leach.py` - LEACH Protocol Simulation
Simulates the LEACH (Low-Energy Adaptive Clustering Hierarchy) routing protocol until all nodes in the network die.

**Default Parameters:**
- Nodes: 100
- Area: 200.0 × 200.0
- Snapshot step: 10 rounds
- Topology step: 10 rounds
- GIF export: enabled

**Usage:**
```bash
# Run with default parameters
python test_leach.py

# Custom configuration with square area
python test_leach.py --nodes 50 --area 150 --max-rounds 500

# Rectangular area (e.g., road/corridor monitoring)
python test_leach.py --nodes 100 --width 200 --height 50

# Custom initial energy (2x default)
python test_leach.py --initial-energy 1.0

# Combined: rectangular area with high energy nodes
python test_leach.py --width 300 --height 100 --initial-energy 1.5 --nodes 150

# Polish language interface
python test_leach.py --language pl

# Save snapshots every 5 rounds, disable topology GIF
python test_leach.py --snapshot-step 5 --no-topo-gif

# Specify custom output directory
python test_leach.py --output-dir my_results
```

**Command-line Arguments:**
```
--nodes NUM              Number of sensor nodes (default: 100)
--area SIZE              Square area side length (default: 200.0)
--width WIDTH            Area width in meters (overrides --area if specified with --height)
--height HEIGHT          Area height in meters (overrides --area if specified with --width)
--initial-energy JOULES  Initial energy per node in Joules (default: 0.5)
--max-rounds N           Maximum rounds to run (default: None = until all nodes die)
--output-dir PATH       Output directory (default: auto-generated Results/run_YYYYMMDD_HHMMSS)
--snapshot-step N       Save alive-nodes plot every N rounds (default: 10, 0 = disabled)
--topo-step N           Save topology every N rounds (default: 10, 0 = disabled)
--snapshot-gif          Create GIF from snapshots (enabled by default)
--no-snapshot-gif       Disable snapshot GIF
--topo-gif              Create GIF from topology (enabled by default)
--no-topo-gif           Disable topology GIF
--backend NAME          Matplotlib backend: Agg, TkAgg, cairo, etc. (default: Agg)
--language LANG          Interface language: eng or pl (default: eng)
```

---

### 2. `test_apteen.py` - APTEEN Protocol Simulation
Simulates the APTEEN (Adaptive Periodic Threshold-sensitive Energy Efficient sensor Network) protocol with configurable threshold parameters.

**Default Parameters:**
- Nodes: 100
- Area: 100.0 × 100.0
- Hard Threshold (HT): 50.0
- Soft Threshold (ST): 2.0
- Count Time (CT): 10 rounds
- Snapshot step: 10 rounds
- Topology step: 10 rounds
- GIF export: enabled

**APTEEN Parameters Explanation:**
- **HT (Hard Threshold)**: Minimum sensor value required to trigger transmission
- **ST (Soft Threshold)**: Minimum change in sensor value for subsequent transmissions
- **CT (Count Time)**: Maximum number of rounds between transmissions

**Usage:**
```bash
# Run with default parameters
python test_apteen.py

# Custom APTEEN configuration
python test_apteen.py --nodes 50 --area 120 --hard-threshold 60 --soft-threshold 3

# Rectangular area for pipeline monitoring
python test_apteen.py --width 500 --height 50 --nodes 200

# High energy nodes for extended lifetime
python test_apteen.py --initial-energy 2.0 --nodes 100

# Combined: large rectangular area with high energy
python test_apteen.py --width 400 --height 150 --initial-energy 1.5 --nodes 250

# Polish language interface
python test_apteen.py --language pl --width 200 --height 100

# Custom configuration
python test_apteen.py --nodes 80 --area 120 --max-rounds 1000

# Configure APTEEN thresholds
python test_apteen.py --hard-threshold 60 --soft-threshold 3 --count-time 15

# TEEN-like behavior (high thresholds, rare periodic updates)
python test_apteen.py --hard-threshold 70 --soft-threshold 5 --count-time 1000

# LEACH-like behavior (low thresholds, frequent updates)
python test_apteen.py --hard-threshold 0.1 --soft-threshold 0.1 --count-time 1

# Save topology every 5 rounds only
python test_apteen.py --topo-step 5 --no-snapshot-gif

# Specify custom output directory
python test_apteen.py --output-dir apteen_results
```

**Command-line Arguments:**
```
--nodes NUM              Number of sensor nodes (default: 100)
--area SIZE              Square area side length (default: 100.0)
--width WIDTH            Area width in meters (overrides --area if specified with --height)
--height HEIGHT          Area height in meters (overrides --area if specified with --width)
--initial-energy JOULES  Initial energy per node in Joules (default: 0.5)
--max-rounds N           Maximum rounds to run (default: None = until all nodes die)
--hard-threshold VAL     Hard threshold (HT) for APTEEN (default: 50.0)
--soft-threshold VAL     Soft threshold (ST) for APTEEN (default: 2.0)
--count-time N           Count time (CT) in rounds for APTEEN (default: 10)
--output-dir PATH       Output directory (default: auto-generated Results/run_YYYYMMDD_HHMMSS)
--snapshot-step N       Save alive-nodes plot every N rounds (default: 10, 0 = disabled)
--topo-step N           Save topology every N rounds (default: 10, 0 = disabled)
--snapshot-gif          Create GIF from snapshots (enabled by default)
--no-snapshot-gif       Disable snapshot GIF
--topo-gif              Create GIF from topology (enabled by default)
--no-topo-gif           Disable topology GIF
--backend NAME          Matplotlib backend: Agg, TkAgg, cairo, etc. (default: Agg)
--language LANG          Interface language: eng or pl (default: eng)
```

---

### 3. `visualize_parameters.py` - APTEEN Parameter Comparison
Runs six different APTEEN configurations and generates comparison charts showing impact of parameters on network lifetime.

**Configurations:**
1. **LEACH-like** (HT=0.1, ST=0.1, TC=1)
2. **TEEN-like** (HT=50, ST=3, TC=1000)
3. **Conservative** (HT=70, ST=5, TC=20)
4. **Aggressive** (HT=40, ST=1, TC=5)
5. **Balanced** (HT=50, ST=2, TC=10)
6. **Adaptive per-cluster** (mixed parameters)

**Default Parameters:**
- Nodes: 30
- Area: 100.0 × 100.0
- Topology step: 50 rounds
- GIF export: enabled
- Output: Results/params_run_YYYYMMDD_HHMMSS

**Usage:**
```bash
# Run with default parameters
python visualize_parameters.py

# Custom configuration with more nodes
python visualize_parameters.py --nodes 50

# Rectangular area comparison
python visualize_parameters.py --width 200 --height 80 --nodes 40

# High energy nodes to see extended lifetime differences
python visualize_parameters.py --initial-energy 2.0 --nodes 50

# Polish language interface with custom area
python visualize_parameters.py --language pl --width 150 --height 100

# Disable GIF and show plot window
python visualize_parameters.py --no-topo-gif --show

# Custom output directory
python visualize_parameters.py --outdir my_params_analysis
```

**Command-line Arguments:**
```
--nodes NUM              Number of sensor nodes per simulation (default: 30)
--area SIZE              Square area side length (default: 100.0)
--width WIDTH            Area width in meters (overrides --area if specified with --height)
--height HEIGHT          Area height in meters (overrides --area if specified with --width)
--initial-energy JOULES  Initial energy per node in Joules (default: 0.5)
--max-rounds N           Maximum rounds per simulation (default: None)
--outdir PATH           Output directory prefix (default: Results/params_run)
--show                  Show plot window (disabled by default)
--no-show               Don't show plot window (enabled by default)
--topo-step N           Save topology snapshots every N rounds (default: 50, 0 = disabled)
--topo-gif              Create topology GIF (enabled by default)
--no-topo-gif           Disable topology GIF
--backend NAME          Matplotlib backend: Agg, TkAgg, cairo, etc. (default: Agg)
--language LANG          Interface language: eng or pl (default: eng)
```

---

## Project Structure

```
wsn_routing/
├── router/                      # Core routing protocols
│   ├── __init__.py
│   ├── node.py                  # Node class with energy models
│   ├── router.py                # Base routing interface
│   ├── routing.py               # Graph algorithms (Prim's MST)
│   ├── common.py                # Shared utilities
│   ├── apteen.py                # APTEEN protocol
│   ├── jso_route.py             # JSO-optimized routing
│   └── leach/                   # LEACH protocol variants
│       ├── __init__.py
│       ├── leach.py             # Standard LEACH
│       ├── leach_pso.py         # PSO-optimized LEACH
│       ├── hierarchical.py      # Hierarchical clustering
│       └── common.py
├── optimizer/                   # Metaheuristic algorithms
│   ├── __init__.py
│   ├── optimizer.py             # JSO & PSO implementations
│   ├── initializer.py           # Chaos-based initialization
│   └── common.py
├── test_leach.py                # LEACH simulation script
├── test_apteen.py               # APTEEN simulation script
├── visualize_parameters.py      # Parameter comparison tool
├── distribution.py              # Topology generation utilities
├── kalman_energy_estimation.py  # Energy prediction demo
├── requirements.txt             # Python dependencies
├── dependencies.txt             # Additional project info
├── GLOSSARY_PL.md              # Polish terminology glossary
├── LICENSE
├── README.md
├── Results/                     # Simulation outputs
├── Dokumentacja/                # LaTeX documentation
└── Theory/                      # Theoretical materials
```

## Output Structure

Each simulation creates the following directory structure:

```
Results/run_YYYYMMDD_HHMMSS/
├── snapshots/
│   ├── test_leach_step_10.png
│   ├── test_leach_step_20.png
│   └── ...
├── topology/
│   ├── topology_leach_10.png
│   ├── topology_leach_20.png
│   └── ...
├── test_leach.png          (final alive-nodes plot)
├── test_leach.gif          (snapshot animation)
└── topology_leach.gif      (topology animation)
```

---

## Environment Variables

You can set default values via environment variables:

```bash
# LEACH/APTEEN tests
export SNAPSHOT_STEP=5      # Default snapshot frequency
export TOPO_STEP=5          # Default topology frequency
export SNAPSHOT_GIF=1       # Enable snapshot GIF (1) or disable (0)
export TOPO_GIF=1           # Enable topology GIF (1) or disable (0)

# Run simulation with environment defaults
python test_leach.py
```

---

## Matplotlib Backends

The `--backend` parameter allows you to choose different rendering backends:

- **Agg** (default): Fast, non-interactive. Best for batch processing and file output
- **TkAgg**: Interactive GUI with zoom/pan capabilities
- **cairo**: Vector graphics backend for publication-quality output
- **Qt5Agg**: Qt-based interactive backend (requires Qt5 plugins)

**Example:**
```bash
python test_leach.py --backend TkAgg
python test_leach.py --backend cairo
```

---

## Requirements

- Python 3.7+
- numpy - Numerical computing
- matplotlib - Plotting and visualization
- imageio - GIF creation
- Pillow - Image processing
- filterpy - Kalman filter implementation
- scienceplots - Publication-quality plot styles
- pyMetaheuristic - PSO implementation

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Dependencies:**
```
numpy
matplotlib
filterpy
scienceplots
imageio
pillow
pyMetaheuristic
```

---

## Examples

### Quick Test Run
```bash
python test_leach.py --nodes 20 --max-rounds 100
```

### Detailed APTEEN Analysis
```bash
python test_apteen.py --nodes 50 --area 150 --snapshot-step 5 --topo-step 5
```

### APTEEN with Custom Thresholds
```bash
# Conservative mode (less transmissions, longer lifetime)
python test_apteen.py --hard-threshold 70 --soft-threshold 5 --count-time 20

# Aggressive mode (more transmissions, shorter lifetime)
python test_apteen.py --hard-threshold 40 --soft-threshold 1 --count-time 5
```

### Compare Parameter Impact
```bash
python visualize_parameters.py --nodes 40 --area 120 --topo-step 25
```

### Disable All Visualizations (Fast Run)
```bash
python test_leach.py --nodes 100 --snapshot-step 0 --topo-step 0
```

### Use Custom Output Directory
```bash
python test_leach.py --output-dir ./my_experiments/exp1
python test_apteen.py --output-dir ./my_experiments/exp2
```

---

## Notes

- Simulations run until all nodes die by default. Use `--max-rounds` to limit execution time.
- Snapshot and topology saving can impact simulation speed. Use larger steps (e.g., 50, 100) for faster runs.
- For headless servers, use `--backend Agg` (default) to avoid display issues.
- GIF generation requires imageio. If not installed, a warning will be shown but simulation continues.
- APTEEN threshold parameters significantly affect network behavior:
  - Higher HT/ST values → fewer transmissions → longer lifetime but less data
  - Lower HT/ST values → more transmissions → shorter lifetime but more data
  - Higher CT values → periodic updates more frequent (LEACH-like)
  - Lower CT values → event-driven updates dominant (TEEN-like)
