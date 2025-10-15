"""Queue distribution strategies."""

from .base import BaseStrategy
from .ringall import RingAllStrategy
from .leastrecent import LeastRecentStrategy
from .fewestcalls import FewestCallsStrategy
from .random import RandomStrategy
from .rrmemory import RoundRobinMemoryStrategy
from .linear import LinearStrategy

__all__ = [
    'BaseStrategy',
    'RingAllStrategy',
    'LeastRecentStrategy',
    'FewestCallsStrategy',
    'RandomStrategy',
    'RoundRobinMemoryStrategy',
    'LinearStrategy'
]

STRATEGY_MAPPING = {
    'ringall': RingAllStrategy,
    'leastrecent': LeastRecentStrategy,
    'fewestcalls': FewestCallsStrategy,
    'random': RandomStrategy,
    'rrmemory': RoundRobinMemoryStrategy,
    'linear': LinearStrategy
}
