# probplots-web — build plan for Claude Code (Sonnet 4.5) — **v2 (adds Joint Distributions)**

## Goal

Create a tiny web app exposing the DLBDSS01-01 statistics helper via a **FastAPI** backend and a minimal **Tailwind (CDN) + vanilla JS** UI. It must run on the Pi (Ubuntu, aarch64) at **127.0.0.1:5009**, fronted by Nginx at **https://probplots.piapps.dev**.

We already have a working CLI at:

```
/home/zk/projects/probplots/bin/dlbdss
```

You will **port its logic into importable functions** and use those inside the API (no shelling out).

> **New in v2:** integrate the **discrete joint-distribution helper** already added under:

```
/home/zk/projects/probplots/stats_helper/joint_dist.py
```

Expose a GET endpoint that consumes a compact query string and returns marginals, conditionals, independence, and moments.

## Environment & Constraints

- Host: Raspberry Pi 5, Ubuntu, Python 3.13 available.
- Project root to create: `/home/zk/projects/probplots-web`
- Bind ONLY to `127.0.0.1:5009`.
- Dependencies: `fastapi`, `uvicorn[standard]`, `numpy`, `scipy`, `matplotlib`.
- Matplotlib must use **Agg** backend (headless).
- Keep code small, readable, and dependency-light.
- Security: **only GET** endpoints; validate inputs; return JSON or PNG.
- Nginx style should mirror `/etc/nginx/sites-available/container.piapps.dev` conventions.

## Deliverables — create this exact tree and files with full contents

```
/home/zk/projects/probplots-web
├── app/
│   ├── __init__.py
│   ├── dlbdss_core.py
│   ├── plotting.py
│   └── api.py
├── static/
│   └── index.html
├── scripts/
│   ├── install.sh
│   ├── run-dev.sh
│   └── make-systemd.sh
├── probplots-web.service
├── nginx-probplots.piapps.dev
└── README.md
```

### 1) `app/dlbdss_core.py`

Port the CLI math into importable functions (no prints). Keep names:

- `binom_pmf(n, p, k) -> float`
- `binom_cdf(n, p, k) -> float`
- `binom_cdf_range(n, p, kmin, kmax) -> float`
- `pois_cdf(lam, k) -> float`
- `geom_pmf(p, k) -> float`  *(k = failures before first success; support 0,1,2,...)*
- `norm_cdf(x, mu, sigma) -> float`
- `norm_inv(p, mu, sigma) -> float`
- `exp_cdf(lam, x) -> float`
- `unif_cdf(a, b, x) -> float`
- `clt(mu, sigma, n, lower, upper) -> float`  *(probability that X̄ is in interval)*

Input validation: raise `ValueError` with friendly messages if constraints fail (e.g., `0<=p<=1`, `sigma>0`, `n>=1`, `b>a`, etc.). Use `numpy`/`scipy.stats` just like the CLI.

> **Joint distributions (from existing project):** Do **not** reimplement. Import from the local project:

```python
# inside app/api.py you will do:
import sys
sys.path.insert(0, "/home/zk/projects/probplots")
from stats_helper import compute_joint_stats  # wraps JointDist.as_dict()
```

Then the API endpoint can call `compute_joint_stats(...)` directly.

### 2) `app/plotting.py`

Return **PNG bytes** using `io.BytesIO`.
Provide:

- `plot_normal_pdf(mu, sigma, w=960, h=480) -> bytes`
- `plot_sim_poisson(n, lam, bins=50, w=960, h=480) -> bytes`
- `plot_sim_binom(n, N, p, bins=50, w=960, h=480) -> bytes`

(Keep the same implementations as v1.)

### 3) `app/api.py` (FastAPI)

Provide endpoints:

- `GET /healthz`
- Numeric: `/api/norm/cdf`, `/api/binom/pmf`, `/api/binom/cdf`, `/api/binom/cdf-range`, `/api/pois/cdf`, `/api/exp/cdf`, `/api/geom/pmf`, `/api/clt`
- **Joint (new):** `GET /api/joint` → parses a compact query param `pairs` into a joint PMF, then returns the `compute_joint_stats(...)` dict.
- Plots (PNG): `/plot/pdf/normal`, `/plot/sim/poisson`, `/plot/sim/binom`
- Root `/` returns `static/index.html`

**Joint endpoint spec (GET):**  
`/api/joint?pairs=0,0,0.1;0,1,0.2;1,0,0.3;1,1,0.4`  

- `pairs` is a semicolon-separated list of triples `x,y,p` (floats).  
- Validate: all p ≥ 0 and **sum ≈ 1** within 1e-10; raise 400 otherwise.  
- Return JSON with keys: `support_X`, `support_Y`, `joint`, `marginal_X`, `marginal_Y`, `independent`, `E`, `Var`, `Cov`, `Corr`.

**Example handler snippet (to implement in `api.py`):**

```python
@app.get("/api/joint")
def api_joint(pairs: str = Query(..., description="x,y,p;...")):
    try:
        items = [t for t in pairs.strip().split(";") if t]
        joint = {}
        for item in items:
            xs, ys, ps = item.split(",")
            x, y, p = float(xs), float(ys), float(ps)
            joint[(x, y)] = p
        # reuse project helper
        from stats_helper import compute_joint_stats
        return JSONResponse(compute_joint_stats(joint))
    except Exception as e:
        _bad(e)
```

### 4) `static/index.html`

Add a tiny panel for the joint endpoint:

```html
<form id="f-joint" class="p-4 rounded-xl bg-white shadow">
  <h3 class="font-semibold mb-2">Joint (discrete)</h3>
  <p class="text-xs text-slate-500 mb-2">pairs: x,y,p;... (must sum to 1)</p>
  <input class="border p-2 rounded w-full" name="pairs"
         value="0,0,0.1;0,1,0.2;1,0,0.3;1,1,0.4">
  <button class="mt-3 px-3 py-2 rounded bg-slate-900 text-white">Compute</button>
  <pre id="r-joint" class="mt-2 text-xs whitespace-pre-wrap break-all"></pre>
</form>
<script>
  (function(){
    const f = document.getElementById('f-joint');
    const out = document.getElementById('r-joint');
    f.addEventListener('submit', async (e) => {
      e.preventDefault();
      out.textContent = '...';
      const q = new URLSearchParams(new FormData(f));
      const r = await fetch('/api/joint?' + q.toString());
      out.textContent = r.ok ? JSON.stringify(await r.json(), null, 2)
                             : ('Error: ' + await r.text());
    });
  })();
</script>
```

*(Keep all other sections from v1.)*

### 5) Scripts, systemd, Nginx

Unchanged from v1. Continue to bind only `127.0.0.1:5009` and proxy via Nginx `probplots.piapps.dev`.

### 6) README

- Mention the new joint endpoint and the input format.

- Include one `curl` example:

  ```bash
  curl -sS 'https://probplots.piapps.dev/api/joint?pairs=0,0,0.1;0,1,0.2;1,0,0.3;1,1,0.4' | jq .
  ```

## Build Steps (Claude, execute in order)

1. Create project tree exactly as specified.

2. Generate files with full contents (v1 + joint pieces above).

3. From `/home/zk/projects/probplots-web`, run:

   ```bash
   bash scripts/install.sh
   bash scripts/run-dev.sh   # local test; Ctrl+C to stop
   ```

4. Install systemd service:

   ```bash
   bash scripts/make-systemd.sh
   ```

5. Install Nginx site file and reload:

   ```bash
   sudo install -m 0644 /home/zk/projects/probplots-web/nginx-probplots.piapps.dev /etc/nginx/sites-available/probplots.piapps.dev
   sudo ln -sf /etc/nginx/sites-available/probplots.piapps.dev /etc/nginx/sites-enabled/probplots.piapps.dev
   sudo nginx -t && sudo systemctl reload nginx
   ```

6. Verify:

   ```bash
   curl -sS https://probplots.piapps.dev/healthz
   curl -sS 'https://probplots.piapps.dev/api/joint?pairs=0,0,0.1;0,1,0.2;1,0,0.3;1,1,0.4' | jq .
   ```

**Success criteria:** site responds over HTTPS via Nginx; JSON endpoints return numbers; plots display; joint endpoint returns keys: `support_X`, `support_Y`, `joint`, `marginal_X`, `marginal_Y`, `independent`, `E`, `Var`, `Cov`, `Corr`.



probplots-web — build plan for Claude Code (Sonnet 4.5)
Goal

Create a tiny web app exposing the DLBDSS01-01 statistics helper via a FastAPI backend and a minimal Tailwind (CDN) + vanilla JS UI. It must run on the Pi (Ubuntu, aarch64) at 127.0.0.1:5009, fronted by Nginx at https://probplots.piapps.dev
.

We already have a working CLI at:

/home/zk/projects/probplots/bin/dlbdss


You will port its logic into importable functions and use those inside the API. No shelling out.

Environment & Constraints

Host: Raspberry Pi 5, Ubuntu, Python 3.13 available.

Project root to create: /home/zk/projects/probplots-web

Bind ONLY to 127.0.0.1:5009.

Dependencies: fastapi, uvicorn[standard], numpy, scipy, matplotlib.

Matplotlib must use Agg backend (headless).

Keep code small, readable, and dependency-light.

Security: no uploads; only GET endpoints; validate inputs; return JSON or PNG.

Nginx style should mirror /etc/nginx/sites-available/container.piapps.dev conventions.

Deliverables — create this exact tree and files with full contents
/home/zk/projects/probplots-web
├── app/
│   ├── __init__.py
│   ├── dlbdss_core.py
│   ├── plotting.py
│   └── api.py
├── static/
│   └── index.html
├── scripts/
│   ├── install.sh
│   ├── run-dev.sh
│   └── make-systemd.sh
├── probplots-web.service
├── nginx-probplots.piapps.dev
└── README.md

1) app/dlbdss_core.py

Task: Read /home/zk/projects/probplots/bin/dlbdss and port the core math into importable functions (no prints). Keep names:

binom_pmf(n, p, k) -> float

binom_cdf(n, p, k) -> float

binom_cdf_range(n, p, kmin, kmax) -> float

pois_cdf(lam, k) -> float

geom_pmf(p, k) -> float (k = failures before first success; support 0,1,2,...)

norm_cdf(x, mu, sigma) -> float

norm_inv(p, mu, sigma) -> float

exp_cdf(lam, x) -> float

unif_cdf(a, b, x) -> float

clt(mu, sigma, n, lower, upper) -> float (probability that X̄ is in interval)

Input validation: raise ValueError with friendly messages if constraints fail (e.g., 0<=p<=1, sigma>0, n>=1, b>a, etc.).

Use numpy/scipy.stats just like the CLI.

Full code to generate (example skeleton — implement bodies fully using scipy/numpy):

# /home/zk/projects/probplots-web/app/dlbdss_core.py
from typing import Optional
import math
import numpy as np
from scipy import stats

def _check_prob(p: float, name="p"):
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"{name} must be in [0,1].")

def _check_pos(x: float, name="value"):
    if not (x > 0):
        raise ValueError(f"{name} must be > 0.")

def binom_pmf(n: int, p: float, k: int) -> float:
    _check_prob(p); 
    if n < 0 or k < 0: raise ValueError("n,k must be >=0.")
    return float(stats.binom.pmf(k, n, p))

def binom_cdf(n: int, p: float, k: int) -> float:
    _check_prob(p); 
    if n < 0 or k < 0: raise ValueError("n,k must be >=0.")
    return float(stats.binom.cdf(k, n, p))

def binom_cdf_range(n: int, p: float, kmin: int, kmax: int) -> float:
    _check_prob(p)
    if n < 0 or kmin < 0 or kmax < 0 or kmax < kmin:
        raise ValueError("n>=0, kmin>=0, kmax>=kmin.")
    hi = stats.binom.cdf(kmax, n, p)
    lo = stats.binom.cdf(kmin-1, n, p)
    return float(hi - lo)

def pois_cdf(lam: float, k: int) -> float:
    _check_pos(lam, "lambda"); 
    if k < 0: raise ValueError("k must be >=0.")
    return float(stats.poisson.cdf(k, lam))

def geom_pmf(p: float, k: int) -> float:
    _check_prob(p)
    if k < 0: raise ValueError("k must be >=0.")
    return float(stats.geom(p=p, loc=-1).pmf(k))

def norm_cdf(x: float, mu: float, sigma: float) -> float:
    _check_pos(sigma, "sigma")
    return float(stats.norm.cdf(x, mu, sigma))

def norm_inv(p: float, mu: float, sigma: float) -> float:
    _check_prob(p); _check_pos(sigma, "sigma")
    return float(stats.norm.ppf(p, mu, sigma))

def exp_cdf(lam: float, x: float) -> float:
    _check_pos(lam, "lambda")
    return float(stats.expon(scale=1/lam).cdf(x))

def unif_cdf(a: float, b: float, x: float) -> float:
    if not (b > a): raise ValueError("Require b > a.")
    return float(stats.uniform(loc=a, scale=b-a).cdf(x))

def clt(mu: float, sigma: float, n: int, lower: float, upper: float) -> float:
    if n <= 0: raise ValueError("n must be >=1.")
    _check_pos(sigma, "sigma")
    se = sigma / np.sqrt(n)
    lo = stats.norm.cdf(lower, mu, se)
    hi = stats.norm.cdf(upper, mu, se)
    return float(hi - lo)

2) app/plotting.py

Return PNG bytes using io.BytesIO.

Provide:

plot_normal_pdf(mu, sigma, w=960, h=480) -> bytes

plot_sim_poisson(n, lam, bins=50, w=960, h=480) -> bytes

plot_sim_binom(n, N, p, bins=50, w=960, h=480) -> bytes

Full code:

# /home/zk/projects/probplots-web/app/plotting.py
import io
import numpy as np
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
from scipy import stats

def _save_png(fig, w, h):
    fig.set_size_inches(w/96, h/96)
    bio = io.BytesIO()
    fig.savefig(bio, format="png", dpi=96, bbox_inches="tight")
    plt.close(fig)
    return bio.getvalue()

def plot_normal_pdf(mu: float, sigma: float, w=960, h=480) -> bytes:
    xs = np.linspace(mu - 4*sigma, mu + 4*sigma, 600)
    ys = stats.norm.pdf(xs, mu, sigma)
    fig, ax = plt.subplots()
    ax.plot(xs, ys, lw=2)
    ax.set_title(f"Normal PDF μ={mu}, σ={sigma}")
    ax.grid(True, alpha=0.3)
    return _save_png(fig, w, h)

def plot_sim_poisson(n: int, lam: float, bins=50, w=960, h=480) -> bytes:
    rng = np.random.default_rng(42)
    data = rng.poisson(lam, size=n)
    fig, ax = plt.subplots()
    ax.hist(data, bins=bins, density=True, alpha=0.6)
    ks = np.arange(0, max(int(lam*4)+1, 15))
    ax.plot(ks, stats.poisson.pmf(ks, lam), lw=2)
    ax.set_title(f"Sim Poisson n={n}, λ={lam}")
    ax.grid(True, alpha=0.3)
    return _save_png(fig, w, h)

def plot_sim_binom(n: int, N: int, p: float, bins=50, w=960, h=480) -> bytes:
    rng = np.random.default_rng(42)
    data = rng.binomial(N, p, size=n)
    fig, ax = plt.subplots()
    ax.hist(data, bins=min(bins, N+1), density=True, alpha=0.6)
    ks = np.arange(0, N+1)
    ax.plot(ks, stats.binom.pmf(ks, N, p), lw=2)
    ax.set_title(f"Sim Binomial n={n}, N={N}, p={p}")
    ax.grid(True, alpha=0.3)
    return _save_png(fig, w, h)

3) app/api.py

FastAPI app with endpoints:

GET /healthz → {ok:true}

Numeric:

/api/norm/cdf?x&mu&sigma

/api/binom/pmf?n&p&k

/api/binom/cdf?n&p&k

/api/binom/cdf-range?n&p&kmin&kmax

/api/pois/cdf?lam&k

/api/exp/cdf?lam&x

/api/geom/pmf?p&k

/api/clt?mu&sigma&n&lower&upper

Plots (PNG):

/plot/pdf/normal?mu&sigma&w&h

/plot/sim/poisson?n&lam&bins&w&h

/plot/sim/binom?n&N&p&bins&w&h

Serve / → static/index.html.

Full code:

# /home/zk/projects/probplots-web/app/api.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import uvicorn
from . import dlbdss_core as core
from . import plotting

def create_app() -> FastAPI:
    app = FastAPI(title="probplots-web", version="0.1")

    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/", include_in_schema=False)
    def root():
        return FileResponse("static/index.html")

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    def _bad(e: Exception):
        raise HTTPException(status_code=400, detail=str(e))

    # --- numeric endpoints ---
    @app.get("/api/norm/cdf")
    def norm_cdf(x: float, mu: float = 0.0, sigma: float = 1.0):
        try: return {"result": core.norm_cdf(x, mu, sigma)}
        except Exception as e: _bad(e)

    @app.get("/api/binom/pmf")
    def binom_pmf(n: int, p: float, k: int):
        try: return {"result": core.binom_pmf(n, p, k)}
        except Exception as e: _bad(e)

    @app.get("/api/binom/cdf")
    def binom_cdf(n: int, p: float, k: int):
        try: return {"result": core.binom_cdf(n, p, k)}
        except Exception as e: _bad(e)

    @app.get("/api/binom/cdf-range")
    def binom_cdf_range(n: int, p: float, kmin: int, kmax: int):
        try: return {"result": core.binom_cdf_range(n, p, kmin, kmax)}
        except Exception as e: _bad(e)

    @app.get("/api/pois/cdf")
    def pois_cdf(lam: float, k: int):
        try: return {"result": core.pois_cdf(lam, k)}
        except Exception as e: _bad(e)

    @app.get("/api/exp/cdf")
    def exp_cdf(lam: float, x: float):
        try: return {"result": core.exp_cdf(lam, x)}
        except Exception as e: _bad(e)

    @app.get("/api/geom/pmf")
    def geom_pmf(p: float, k: int):
        try: return {"result": core.geom_pmf(p, k)}
        except Exception as e: _bad(e)

    @app.get("/api/clt")
    def clt(mu: float, sigma: float, n: int, lower: float, upper: float):
        try: return {"result": core.clt(mu, sigma, n, lower, upper)}
        except Exception as e: _bad(e)

    # --- plot endpoints (PNG) ---
    def clamp(val, lo, hi, default):
        if val is None: return default
        return max(lo, min(hi, val))

    @app.get("/plot/pdf/normal")
    def plot_normal(mu: float = 0.0, sigma: float = 1.0,
                    w: int = Query(960, ge=300, le=1600),
                    h: int = Query(480, ge=200, le=1200)):
        try:
            png = plotting.plot_normal_pdf(mu, sigma, w, h)
            return StreamingResponse(iter([png]), media_type="image/png")
        except Exception as e: _bad(e)

    @app.get("/plot/sim/poisson")
    def plot_sim_poisson(n: int = Query(50000, ge=1, le=5_000_000),
                         lam: float = Query(3.0, gt=0),
                         bins: int = Query(50, ge=5, le=200),
                         w: int = Query(960, ge=300, le=1600),
                         h: int = Query(480, ge=200, le=1200)):
        try:
            png = plotting.plot_sim_poisson(n, lam, bins, w, h)
            return StreamingResponse(iter([png]), media_type="image/png")
        except Exception as e: _bad(e)

    @app.get("/plot/sim/binom")
    def plot_sim_binom(n: int = Query(50000, ge=1, le=5_000_000),
                       N: int = Query(20, ge=1, le=10_000),
                       p: float = Query(0.3, ge=0.0, le=1.0),
                       bins: int = Query(50, ge=5, le=400),
                       w: int = Query(960, ge=300, le=1600),
                       h: int = Query(480, ge=200, le=1200)):
        try:
            png = plotting.plot_sim_binom(n, N, p, bins, w, h)
            return StreamingResponse(iter([png]), media_type="image/png")
        except Exception as e: _bad(e)

    return app

if __name__ == "__main__":
    uvicorn.run("app.api:create_app", factory=True, host="127.0.0.1", port=5009)

4) static/index.html

Tailwind CDN + simple forms.

Use fetch() for JSON endpoints; set <img src="..."> for plots.

Full code (concise UI):

<!-- /home/zk/projects/probplots-web/static/index.html -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>probplots</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-900">
  <div class="max-w-4xl mx-auto p-6 space-y-8">
    <header>
      <h1 class="text-3xl font-bold">probplots — DLBDSS01-01 helper</h1>
      <p class="text-sm text-slate-600">FastAPI backend @ 127.0.0.1:5009</p>
    </header>

    <section class="space-y-4">
      <h2 class="text-xl font-semibold">Quick numeric queries</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

        <!-- Normal CDF -->
        <form id="f-norm" class="p-4 rounded-xl bg-white shadow">
          <h3 class="font-semibold mb-2">Normal CDF</h3>
          <div class="grid grid-cols-3 gap-2">
            <input class="border p-2 rounded" name="x" placeholder="x" value="1.96">
            <input class="border p-2 rounded" name="mu" placeholder="mu" value="0">
            <input class="border p-2 rounded" name="sigma" placeholder="sigma" value="1">
          </div>
          <button class="mt-3 px-3 py-2 rounded bg-slate-900 text-white">Compute</button>
          <div class="mt-2 text-sm" id="r-norm"></div>
        </form>

        <!-- Binomial PMF -->
        <form id="f-binom-pmf" class="p-4 rounded-xl bg-white shadow">
          <h3 class="font-semibold mb-2">Binomial PMF</h3>
          <div class="grid grid-cols-3 gap-2">
            <input class="border p-2 rounded" name="n" placeholder="n" value="10">
            <input class="border p-2 rounded" name="p" placeholder="p" value="0.3">
            <input class="border p-2 rounded" name="k" placeholder="k" value="4">
          </div>
          <button class="mt-3 px-3 py-2 rounded bg-slate-900 text-white">Compute</button>
          <div class="mt-2 text-sm" id="r-binom-pmf"></div>
        </form>

        <!-- Binomial CDF range -->
        <form id="f-binom-range" class="p-4 rounded-xl bg-white shadow">
          <h3 class="font-semibold mb-2">Binomial CDF (range)</h3>
          <div class="grid grid-cols-4 gap-2">
            <input class="border p-2 rounded" name="n" placeholder="n" value="10">
            <input class="border p-2 rounded" name="p" placeholder="p" value="0.3">
            <input class="border p-2 rounded" name="kmin" placeholder="kmin" value="3">
            <input class="border p-2 rounded" name="kmax" placeholder="kmax" value="7">
          </div>
          <button class="mt-3 px-3 py-2 rounded bg-slate-900 text-white">Compute</button>
          <div class="mt-2 text-sm" id="r-binom-range"></div>
        </form>

        <!-- CLT -->
        <form id="f-clt" class="p-4 rounded-xl bg-white shadow">
          <h3 class="font-semibold mb-2">CLT interval P( lower &lt; X̄ &lt; upper )</h3>
          <div class="grid grid-cols-5 gap-2">
            <input class="border p-2 rounded" name="mu" placeholder="mu" value="100">
            <input class="border p-2 rounded" name="sigma" placeholder="sigma" value="15">
            <input class="border p-2 rounded" name="n" placeholder="n" value="36">
            <input class="border p-2 rounded" name="lower" placeholder="lower" value="95">
            <input class="border p-2 rounded" name="upper" placeholder="upper" value="105">
          </div>
          <button class="mt-3 px-3 py-2 rounded bg-slate-900 text-white">Compute</button>
          <div class="mt-2 text-sm" id="r-clt"></div>
        </form>

      </div>
    </section>

    <section class="space-y-4">
      <h2 class="text-xl font-semibold">Plots</h2>
      <div class="grid grid-cols-1 gap-4">

        <form id="f-plot-norm" class="p-4 rounded-xl bg-white shadow">
          <h3 class="font-semibold mb-2">Normal PDF</h3>
          <div class="grid grid-cols-4 gap-2">
            <input class="border p-2 rounded" name="mu" placeholder="mu" value="0">
            <input class="border p-2 rounded" name="sigma" placeholder="sigma" value="1">
            <input class="border p-2 rounded" name="w" placeholder="w" value="960">
            <input class="border p-2 rounded" name="h" placeholder="h" value="480">
          </div>
          <button class="mt-3 px-3 py-2 rounded bg-slate-900 text-white">Render</button>
          <img id="img-normal" class="mt-3 rounded border" alt="normal pdf"/>
        </form>

        <form id="f-plot-binom" class="p-4 rounded-xl bg-white shadow">
          <h3 class="font-semibold mb-2">Sim Binomial</h3>
          <div class="grid grid-cols-6 gap-2">
            <input class="border p-2 rounded" name="n" placeholder="n" value="50000">
            <input class="border p-2 rounded" name="N" placeholder="N" value="20">
            <input class="border p-2 rounded" name="p" placeholder="p" value="0.3">
            <input class="border p-2 rounded" name="bins" placeholder="bins" value="50">
            <input class="border p-2 rounded" name="w" placeholder="w" value="960">
            <input class="border p-2 rounded" name="h" placeholder="h" value="480">
          </div>
          <button class="mt-3 px-3 py-2 rounded bg-slate-900 text-white">Render</button>
          <img id="img-binom" class="mt-3 rounded border" alt="sim binom"/>
        </form>

        <form id="f-plot-pois" class="p-4 rounded-xl bg-white shadow">
          <h3 class="font-semibold mb-2">Sim Poisson</h3>
          <div class="grid grid-cols-6 gap-2">
            <input class="border p-2 rounded" name="n" placeholder="n" value="50000">
            <input class="border p-2 rounded" name="lam" placeholder="λ" value="3">
            <input class="border p-2 rounded" name="bins" placeholder="bins" value="50">
            <input class="border p-2 rounded" name="w" placeholder="w" value="960">
            <input class="border p-2 rounded" name="h" placeholder="h" value="480">
          </div>
          <button class="mt-3 px-3 py-2 rounded bg-slate-900 text-white">Render</button>
          <img id="img-pois" class="mt-3 rounded border" alt="sim poisson"/>
        </form>

      </div>
    </section>
  </div>

  <script>
    async function handleJSON(formId, resId, url) {
      const el = document.getElementById(formId);
      el.addEventListener('submit', async (e) => {
        e.preventDefault();
        const params = new URLSearchParams(new FormData(el));
        const out = document.getElementById(resId);
        out.textContent = '...';
        const r = await fetch(url + '?' + params.toString());
        if (!r.ok) { out.textContent = 'Error: ' + (await r.text()); return; }
        const j = await r.json();
        out.textContent = j.result;
      });
    }
    async function handleIMG(formId, imgId, url) {
      const el = document.getElementById(formId);
      el.addEventListener('submit', (e) => {
        e.preventDefault();
        const params = new URLSearchParams(new FormData(el));
        document.getElementById(imgId).src = url + '?' + params.toString();
      });
    }

    handleJSON('f-norm','r-norm','/api/norm/cdf');
    handleJSON('f-binom-pmf','r-binom-pmf','/api/binom/pmf');
    handleJSON('f-binom-range','r-binom-range','/api/binom/cdf-range');
    handleJSON('f-clt','r-clt','/api/clt');

    handleIMG('f-plot-norm','img-normal','/plot/pdf/normal');
    handleIMG('f-plot-binom','img-binom','/plot/sim/binom');
    handleIMG('f-plot-pois','img-pois','/plot/sim/poisson');
  </script>
</body>
</html>

5) scripts/install.sh
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn[standard] numpy scipy matplotlib
echo "OK: venv ready."

6) scripts/run-dev.sh
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
exec uvicorn app.api:create_app --factory --host 127.0.0.1 --port 5009

7) scripts/make-systemd.sh
#!/usr/bin/env bash
set -euo pipefail
APPDIR="/home/zk/projects/probplots-web"
cat > "$APPDIR/probplots-web.service" <<'UNIT'
[Unit]
Description=probplots web (FastAPI)
After=network-online.target
Wants=network-online.target

[Service]
User=zk
Group=zk
WorkingDirectory=/home/zk/projects/probplots-web
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/zk/projects/probplots-web/.venv/bin/uvicorn app.api:create_app --factory --host 127.0.0.1 --port 5009
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

sudo install -m 0644 "$APPDIR/probplots-web.service" /etc/systemd/system/probplots-web.service
sudo systemctl daemon-reload
sudo systemctl enable --now probplots-web
systemctl status --no-pager probplots-web || true

8) probplots-web.service

(same content as generated in the script; create as a tracked file too)

9) nginx-probplots.piapps.dev

Create /home/zk/projects/probplots-web/nginx-probplots.piapps.dev with this complete site file mirroring house style and pointing to 127.0.0.1:5009:

# =========================
# probplots.piapps.dev  (SPA served by FastAPI; same-origin API)
# =========================

map $http_origin $cors_allow_probplots {
  default "";
  "~^https://probplots\.piapps\.dev$"        $http_origin;
  "~^https://(www\.)?containeryard\.org$"    $http_origin; # optional
}

server {
  listen 80;
  server_name probplots.piapps.dev;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl;
  http2 on;
  server_name probplots.piapps.dev;

  ssl_certificate     /etc/letsencrypt/live/piapps.dev-0001/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/piapps.dev-0001/privkey.pem;
  include /etc/letsencrypt/options-ssl-nginx.conf;
  ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

  include /etc/nginx/conf.d/cloudflare_real_ip.conf;

  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

  # API first
  location /api/ {
    add_header Access-Control-Allow-Origin $cors_allow_probplots always;
    add_header Access-Control-Allow-Credentials "true" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With, X-CSRF-Token" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
    add_header Vary "Origin" always;

    if ($request_method = OPTIONS) { return 204; }

    proxy_pass http://127.0.0.1:5009;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;

    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host  $host;
    proxy_set_header X-Forwarded-Port  443;

    proxy_set_header Origin $http_origin;

    proxy_read_timeout    75s;
    proxy_send_timeout    75s;
    proxy_connect_timeout 15s;

    client_max_body_size  10m;
  }

  # Health passthrough
  location = /health {
    proxy_pass http://127.0.0.1:5009/healthz;
    proxy_http_version 1.1;
    proxy_set_header Connection "";

    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    expires off;
    add_header Cache-Control "no-cache, no-store, must-revalidate" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;
  }

  # Edge health (always-200)
  location = /healthz {
    default_type application/json;
    add_header Cache-Control "no-cache, no-store, must-revalidate" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;
    return 200 '{"status":"ok","host":"$hostname","time":"$time_iso8601"}';
  }

  # SPA & static proxied to FastAPI
  location / {
    add_header Cache-Control "no-cache";
    proxy_pass http://127.0.0.1:5009;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  # Harden
  location ~* (?i)(^|/)(\.env|\.git|\.htaccess|\.DS_Store|\.aws|credentials|composer\.json)$ { return 403; }
  location ~* (?i)\.(ya?ml|ini|sql|bak|old|log|config)$ { return 403; }

  access_log /var/log/nginx/probplots.piapps.dev.access.log;
  error_log  /var/log/nginx/probplots.piapps.dev.error.log warn;
}

10) README.md

Include install, dev, systemd, and Nginx steps, plus example curl tests.

Full code:

# probplots-web

FastAPI + Tailwind UI exposing DLBDSS01-01 helpers on 127.0.0.1:5009.

## Install
```bash
/home/zk/projects/probplots-web/scripts/install.sh

Run (dev)
/home/zk/projects/probplots-web/scripts/run-dev.sh


Open https://probplots.piapps.dev/
 (after Nginx is configured).

Systemd
/home/zk/projects/probplots-web/scripts/make-systemd.sh

Nginx

Copy nginx-probplots.piapps.dev to /etc/nginx/sites-available/, enable, test, reload:

sudo install -m 0644 /home/zk/projects/probplots-web/nginx-probplots.piapps.dev /etc/nginx/sites-available/probplots.piapps.dev
sudo ln -sf /etc/nginx/sites-available/probplots.piapps.dev /etc/nginx/sites-enabled/probplots.piapps.dev
sudo nginx -t && sudo systemctl reload nginx

Health checks
curl -sS https://probplots.piapps.dev/healthz
curl -sS https://probplots.piapps.dev/health

API examples
curl -sS 'https://probplots.piapps.dev/api/norm/cdf?x=1.96&mu=0&sigma=1'
curl -sS 'https://probplots.piapps.dev/api/binom/pmf?n=10&p=0.3&k=4'
curl -sS 'https://probplots.piapps.dev/api/binom/cdf-range?n=10&p=0.3&kmin=3&kmax=7'


---

## Build Steps (Claude, execute in order)

1. **Create project tree** exactly as specified.
2. Generate all files with the **full contents** above.
3. From `/home/zk/projects/probplots-web`, run:
   ```bash
   bash scripts/install.sh
   bash scripts/run-dev.sh   # for a local test; Ctrl+C to stop


Install systemd service:

bash scripts/make-systemd.sh


Install Nginx site file and reload:

sudo install -m 0644 /home/zk/projects/probplots-web/nginx-probplots.piapps.dev /etc/nginx/sites-available/probplots.piapps.dev
sudo ln -sf /etc/nginx/sites-available/probplots.piapps.dev /etc/nginx/sites-enabled/probplots.piapps.dev
sudo nginx -t && sudo systemctl reload nginx


Verify:

curl -sS https://probplots.piapps.dev/healthz
curl -sS 'https://probplots.piapps.dev/api/norm/cdf?x=1.96&mu=0&sigma=1'


Success criteria: site responds over HTTPS via Nginx; JSON endpoints return numbers; plot forms display images; service restarts automatically on reboot.
