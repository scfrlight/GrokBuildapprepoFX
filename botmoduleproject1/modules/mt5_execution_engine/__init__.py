"""Sequence 11 — MT5 Demo execution & exit engine.

Master Orchestration title: "PM6 MT5 Execution & Exit Engine".
That title is NOT a package name. `pm6_post_trade` remains PM6.
This package is `mt5_execution_engine`. See docs/MODULE_NUMBERING_MAP.md.

Demo-only. Tickets are DEMO-*. Live is refused. Not broker truth.
"""

from botmoduleproject1.modules.mt5_execution_engine.demo_routing import DemoRouter
from botmoduleproject1.modules.mt5_execution_engine.exit_engine import ExitEngine, ExitState
from botmoduleproject1.modules.mt5_execution_engine.module import MT5ExecutionEngineModule

__all__ = ["DemoRouter", "ExitEngine", "ExitState", "MT5ExecutionEngineModule"]
