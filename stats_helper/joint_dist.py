from typing import Dict, Tuple
import math

Prob = float
JointPMF = Dict[Tuple[float, float], Prob]  # {(x,y): p}

class JointDist:
    def __init__(self, joint: JointPMF, tol: float = 1e-12):
        self.joint = {k: float(v) for k, v in joint.items()}
        self.tol = tol
        self._xs = sorted({x for (x, _) in joint})
        self._ys = sorted({y for (_, y) in joint})
        self._validate()
        self.fx = self._marginal_x()
        self.fy = self._marginal_y()

    # ---------- core checks ----------
    def _validate(self):
        if any(p < -self.tol for p in self.joint.values()):
            raise ValueError("Joint PMF has negative probabilities.")
        total = sum(self.joint.values())
        if abs(total - 1.0) > 1e-10:
            raise ValueError(f"Joint PMF must sum to 1 (got {total:.12g}).")

    # ---------- marginals ----------
    def _marginal_x(self) -> Dict[float, Prob]:
        out = {x: 0.0 for x in self._xs}
        for (x, y), p in self.joint.items():
            out[x] += p
        return out

    def _marginal_y(self) -> Dict[float, Prob]:
        out = {y: 0.0 for y in self._ys}
        for (x, y), p in self.joint.items():
            out[y] += p
        return out

    # ---------- conditionals ----------
    def conditional_x_given_y(self, y: float) -> Dict[float, Prob]:
        py = self.fy.get(y, 0.0)
        if py <= self.tol:
            raise ZeroDivisionError("P(Y=y)=0; conditional undefined.")
        return {x: self.joint.get((x, y), 0.0) / py for x in self._xs}

    def conditional_y_given_x(self, x: float) -> Dict[float, Prob]:
        px = self.fx.get(x, 0.0)
        if px <= self.tol:
            raise ZeroDivisionError("P(X=x)=0; conditional undefined.")
        return {y: self.joint.get((x, y), 0.0) / px for y in self._ys}

    # ---------- independence test ----------
    def is_independent(self) -> bool:
        for (x, y), p in self.joint.items():
            if abs(p - self.fx[x]*self.fy[y]) > 1e-9:
                return False
        for x in self._xs:
            for y in self._ys:
                p = self.joint.get((x, y), 0.0)
                if abs(p - self.fx[x]*self.fy[y]) > 1e-9:
                    return False
        return True

    # ---------- expectations & moments ----------
    def E(self):
        ex = sum(x * px for x, px in self.fx.items())
        ey = sum(y * py for y, py in self.fy.items())
        return ex, ey

    def EXY(self) -> float:
        return sum(x*y*p for (x, y), p in self.joint.items())

    def Var(self):
        ex, ey = self.E()
        ex2 = sum((x**2)*px for x, px in self.fx.items())
        ey2 = sum((y**2)*py for y, py in self.fy.items())
        return (ex2 - ex**2, ey2 - ey**2)

    def Cov(self) -> float:
        ex, ey = self.E()
        return self.EXY() - ex*ey

    def Corr(self) -> float:
        vx, vy = self.Var()
        if vx <= self.tol or vy <= self.tol:
            raise ZeroDivisionError("Zero variance; correlation undefined.")
        return self.Cov() / math.sqrt(vx*vy)

    # ---------- JSON-friendly dump ----------
    def as_dict(self):
        vx, vy = self.Var()
        corr = None
        if vx > self.tol and vy > self.tol:
            corr = self.Corr()
        return {
            "support_X": self._xs,
            "support_Y": self._ys,
            "joint": [{ "x": x, "y": y, "p": p } for (x,y), p in sorted(self.joint.items())],
            "marginal_X": self.fx,
            "marginal_Y": self.fy,
            "independent": self.is_independent(),
            "E": {"EX": self.E()[0], "EY": self.E()[1]},
            "Var": {"VarX": vx, "VarY": vy},
            "Cov": self.Cov(),
            "Corr": corr
        }
