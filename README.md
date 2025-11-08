# probplots — DLBDSS01-01 Statistics Helper (CLI + Plots + Joint API)

Course-aligned tools for **Probability & Descriptive Statistics (DLBDSS01‑01)**.  
Runs great on Ubuntu and Raspberry Pi 5. Includes closed‑form distribution queries, inequalities/CLT helpers, simulations, **headless plotting**, and **discrete joint-distribution analysis**.

> **Main entry (CLI):** `/home/zk/projects/probplots/dlbdss`  
> **Python API (package):** `/home/zk/projects/probplots/stats_helper`  
> No need to activate the venv for the CLI; the shebang points to the project’s Python.

---

## Features

- Probability basics: `factorial`, `perm`, `comb`
- Distributions (PMF/CDF/quantiles): **Binomial, Poisson, Geometric, Normal, Exponential, Uniform**
- Inequalities & theorems: **Markov, Chebyshev, CLT** (sample‑mean probability on an interval)
- Simulations with visual overlays: `sim-hist` (Normal, Binomial, Poisson)
- **Headless plots** via `--out file.png` (automatic Agg backend when no `DISPLAY`)
- **Joint distributions (discrete)**: validate joint PMF, **marginals**, **conditionals**, **independence test**, and **E, Var, Cov, Corr** from a joint table

---

## Project Layout

```
/home/zk/projects/probplots
├── .venv/
├── bin/
│   └── dlbdss
├── dlbdss                  # convenience launcher (execs bin/dlbdss)
└── stats_helper/
    ├── __init__.py        # exports compute_joint_stats(...)
    └── joint_dist.py      # JointDist class
```

---

## Install (one‑time)

```bash
/usr/bin/mkdir -p /home/zk/projects/probplots/bin
/usr/bin/python3 -m venv /home/zk/projects/probplots/.venv
source /home/zk/projects/probplots/.venv/bin/activate
/home/zk/projects/probplots/.venv/bin/pip install --upgrade pip
/home/zk/projects/probplots/.venv/bin/pip install --only-binary=:all: numpy scipy matplotlib
```

---

## Usage Cheat‑Sheet (CLI)

```bash
# Normal CDF: P(X ≤ 1.96) for N(0,1)
/home/zk/projects/probplots/dlbdss norm-cdf --x 1.96 --mu 0 --sigma 1

# Binomial: P(X = 4) for X~Bin(n=10,p=0.3)
/home/zk/projects/probplots/dlbdss binom-pmf --n 10 --p 0.3 --k 4

# Binomial range: P(3 ≤ X ≤ 7)
/home/zk/projects/probplots/dlbdss binom-cdf --n 10 --p 0.3 --kmin 3 --kmax 7

# Poisson: P(X ≤ 2) when λ=3.5
/home/zk/projects/probplots/dlbdss pois-cdf --lam 3.5 --k 2

# Exponential CDF at x=5 with λ=0.4
/home/zk/projects/probplots/dlbdss exp-cdf --x 5 --lam 0.4

# Geometric pmf (k failures before 1st success), p=0.3, k=2
/home/zk/projects/probplots/dlbdss geom-pmf --p 0.3 --k 2

# Inequalities (bounds)
/home/zk/projects/probplots/dlbdss markov --mean 40 --t 240
/home/zk/projects/probplots/dlbdss chebyshev --sigma 2.1 --t 3

# CLT: P(95 < X̄ < 105) for μ=100, σ=15, n=36
/home/zk/projects/probplots/dlbdss clt --mu 100 --sigma 15 --n 36 --lower 95 --upper 105
```

---

## Python API — Joint Distributions (Discrete)

```python
import sys
sys.path.insert(0, "/home/zk/projects/probplots")
from stats_helper import compute_joint_stats

# 2×2 example (sums to 1.0):
joint = {(0,0):0.1, (0,1):0.2, (1,0):0.3, (1,1):0.4}
out = compute_joint_stats(joint)
print(out["marginal_X"])  # {0: 0.3, 1: 0.7}
print(out["marginal_Y"])  # {0: 0.4, 1: 0.6}
print(out["independent"]) # False
print(out["Cov"], out["Corr"])
```

**Keys in result:** `support_X`, `support_Y`, `joint`, `marginal_X`, `marginal_Y`, `independent`, `E`, `Var`, `Cov`, `Corr`.

### FX‑991EX Cross‑Check (Exam Habit)

- Build marginals: sum rows/columns.
- Check independence by comparing `f_{X,Y}(x,y)` vs `f_X(x)f_Y(y)` for each cell.
- Verify `E[X] = Σ_x x f_X(x)`, `E[Y] = Σ_y y f_Y(y)`; `Cov = E[XY] - E[X]E[Y]`.

---

## Plots (headless‑friendly)

If you’re on SSH, pass `--out` to save PNGs.

```bash
/home/zk/projects/probplots/dlbdss plot-pdf --dist normal --mu 0 --sigma 1   --out /home/zk/projects/probplots/stdnormal.png

/home/zk/projects/probplots/dlbdss sim-hist --dist normal --n 50000 --mu 0 --sigma 1   --bins 60 --out /home/zk/projects/probplots/sim_norm.png

/home/zk/projects/probplots/dlbdss sim-hist --dist binom --n 50000 --N 20 --p 0.3   --out /home/zk/projects/probplots/sim_binom.png

/home/zk/projects/probplots/dlbdss sim-hist --dist poisson --n 50000 --lam 3   --out /home/zk/projects/probplots/sim_pois.png
```

---

## probplots‑web (Thin UI) — Plan

A separate repo will host a **FastAPI** backend + **Tailwind** UI on `127.0.0.1:5009`, proxied at `https://probplots.piapps.dev`.  
**v2 adds** `/api/joint?pairs=...` endpoint that calls `stats_helper.compute_joint_stats(...)`.  
See `plan.v2.md` for full build steps.

---

## Performance Notes (Pi 5)

- Closed‑form queries are ms‑level; tiny RAM.

- Simulation memory ≈ `8 bytes × n` for float64 (half for float32).

- Headless plotting is automatic when no `DISPLAY`.

- Keep the box responsive:

  ```bash
  export OPENBLAS_NUM_THREADS=1
  ```

---

## Changelog

- **v0.3** — Added `stats_helper/JointDist` and `compute_joint_stats(...)`; updated docs.
- **v0.2** — Headless plotting, float32 option for simulations, project‑local launcher
- **v0.1** — Core distributions, inequalities, CLT, basic plots/sims

---

## License

MIT (placeholder).









# probplots — DLBDSS01-01 Statistics Helper (CLI + Plots)

Course-aligned command‑line tools for **Probability & Descriptive Statistics (DLBDSS01‑01)**.  
Runs great on Ubuntu and Raspberry Pi 5. Includes closed‑form distribution queries, inequalities/CLT helpers, simulations, and **headless plotting** for remote SSH sessions.

> **Main entry:** `/home/zk/projects/probplots/dlbdss`  
> No need to activate the venv; the shebang points to the project’s Python.

---

## Features

- Probability basics: `factorial`, `perm`, `comb`  
- Distributions (PMF/CDF/quantiles): **Binomial, Poisson, Geometric, Normal, Exponential, Uniform**
- Inequalities & theorems: **Markov, Chebyshev, CLT** (sample‑mean probability on an interval)
- Simulations with visual overlays: `sim-hist` (Normal, Binomial, Poisson)
- **Headless plots** via `--out file.png` (automatic Agg backend when no `DISPLAY`)
- Pi‑friendly: optional `--dtype float32` to halve RAM in large Normal simulations

---

## Project Layout

```
/home/zk/projects/probplots
├── .venv/                # project virtualenv (created once)
├── bin/
│   └── dlbdss            # CLI entry point (shebang -> .venv/python)
├── dlbdss                # convenience launcher (execs bin/dlbdss)
└── README.md             # this file
```

---

## Requirements

- Python 3.10+ (tested with 3.13 on aarch64)
- Packages: `numpy`, `scipy`, `matplotlib` (prebuilt wheels on Ubuntu/PI aarch64)

---

## Install (one‑time)

```bash
# Create project
/usr/bin/mkdir -p /home/zk/projects/probplots/bin

# Virtualenv
/usr/bin/python3 -m venv /home/zk/projects/probplots/.venv
source /home/zk/projects/probplots/.venv/bin/activate

# Fast wheel installs
/home/zk/projects/probplots/.venv/bin/pip install --upgrade pip
/home/zk/projects/probplots/.venv/bin/pip install --only-binary=:all: numpy scipy matplotlib
```

Add the CLI script to `/home/zk/projects/probplots/bin/dlbdss` (already present in this setup).

For a project‑local launcher, `dlbdss` exists at the project root and simply execs `bin/dlbdss`.

---

## Usage Cheat‑Sheet

### Quick numeric queries

```bash
# Normal CDF: P(X ≤ 1.96) for N(0,1)
/home/zk/projects/probplots/dlbdss norm-cdf --x 1.96 --mu 0 --sigma 1

# Binomial: P(X = 4) for X~Bin(n=10,p=0.3)
/home/zk/projects/probplots/dlbdss binom-pmf --n 10 --p 0.3 --k 4

# Binomial range: P(3 ≤ X ≤ 7)
/home/zk/projects/probplots/dlbdss binom-cdf --n 10 --p 0.3 --kmin 3 --kmax 7

# Poisson: P(X ≤ 2) when λ=3.5
/home/zk/projects/probplots/dlbdss pois-cdf --lam 3.5 --k 2

# Exponential CDF at x=5 with λ=0.4
/home/zk/projects/probplots/dlbdss exp-cdf --x 5 --lam 0.4

# Geometric pmf (k failures before 1st success), p=0.3, k=2
/home/zk/projects/probplots/dlbdss geom-pmf --p 0.3 --k 2

# Inequalities (bounds)
/home/zk/projects/probplots/dlbdss markov --mean 40 --t 240
/home/zk/projects/probplots/dlbdss chebyshev --sigma 2.1 --t 3

# CLT: P(95 < X̄ < 105) for μ=100, σ=15, n=36
/home/zk/projects/probplots/dlbdss clt --mu 100 --sigma 15 --n 36 --lower 95 --upper 105
```

### Plots (headless‑friendly)

If you’re on SSH, pass `--out` to save PNGs.

```bash
# Standard normal PDF → PNG
/home/zk/projects/probplots/dlbdss plot-pdf --dist normal --mu 0 --sigma 1 \
  --out /home/zk/projects/probplots/stdnormal.png

# Simulate Normal and overlay theory
/home/zk/projects/probplots/dlbdss sim-hist --dist normal --n 50000 --mu 0 --sigma 1 \
  --bins 60 --out /home/zk/projects/probplots/sim_norm.png

# Lighter RAM for very large n (float32)
/home/zk/projects/probplots/dlbdss sim-hist --dist normal --n 2000000 --mu 0 --sigma 1 \
  --dtype float32 --bins 80 --out /home/zk/projects/probplots/sim_norm_big.png

# Binomial and Poisson sims
/home/zk/projects/probplots/dlbdss sim-hist --dist binom --n 50000 --N 20 --p 0.3 \
  --out /home/zk/projects/probplots/sim_binom.png

/home/zk/projects/probplots/dlbdss sim-hist --dist poisson --n 50000 --lam 3 \
  --out /home/zk/projects/probplots/sim_pois.png
```

### Help

```bash
/home/zk/projects/probplots/dlbdss --help
/home/zk/projects/probplots/dlbdss norm-cdf --help
/home/zk/projects/probplots/dlbdss sim-hist --help
```

---

## FX‑991EX Cross‑Check (Exam Habit)

- **DIST → NORM/CD/INV** for `norm-cdf`, `norm-inv` verification
- **BINM / POIS** for binomial/poisson checks
- CLT queries operate on the **sample mean** \(X̄\) with SE = σ/√n

---

## Performance Notes (Pi 5)

- Closed‑form queries are millisecond‑level, tiny RAM.

- Simulation memory ≈ `8 bytes × n` for float64 (half for float32).  
  Examples: `n=1e5 → ~0.8 MB`, `n=1e6 → ~8 MB`, `n=1e7 → ~80 MB`.

- Headless plotting is automatic when no `DISPLAY`.  

- Keep the box responsive:

  ```bash
  export OPENBLAS_NUM_THREADS=1
  ```

---

## Roadmap

- `table-expect` — E[X], Var(X) from value/probability lists
- `joint` — marginalization + independence check from a joint table
- `--save-csv` — dump simulation samples to a CSV
- Add Beta/Gamma if they appear in course exercises

---

## Changelog

- **v0.2** — Headless plotting, float32 option for simulations, project‑local launcher
- **v0.1** — Core distributions, inequalities, CLT, basic plots/sims

---

## License

MIT (placeholder).

---

## Acknowledgments

Built for DLBDSS01‑01 study workflow. Plots & sims inspired by the “simulate‑and‑compare” approach for intuition building.
