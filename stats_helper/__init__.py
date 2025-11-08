# makes stats_helper a package
from .joint_dist import JointDist

def compute_joint_stats(joint):
    """
    joint: dict with keys (x,y) -> p, where x,y are numbers and p>=0 and sum p == 1
    returns: JSON-friendly dict with marginals, conditionals (via methods), moments, etc.
    """
    return JointDist(joint).as_dict()
