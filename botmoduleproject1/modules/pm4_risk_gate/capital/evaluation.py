"""Deterministic capital evaluation pipeline. Fail closed. Never an order."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from threading import Lock
from typing import Any
from uuid import uuid4

from botmoduleproject1.contracts.v1.pm4_capital import (
    CapitalDecisionState,
    CapitalEvaluationResult,
    CheckOutcome,
    CheckStatus,
    RiskApprovedExecutableIntent,
    RiskDecision,
    RiskEvaluationRequest,
    RiskRejection,
)
from botmoduleproject1.contracts.v1.time import ensure_aware_utc
from botmoduleproject1.modules.pm4_risk_gate.capital.catalog import CHECK_CATALOG
from botmoduleproject1.modules.pm4_risk_gate.capital.checks import run_checks
from botmoduleproject1.modules.pm4_risk_gate.capital.drawdown_ledger import DrawdownLedger
from botmoduleproject1.modules.pm4_risk_gate.capital.hashing import canonical_hash
from botmoduleproject1.modules.pm4_risk_gate.capital.metrics import CapitalMetrics
from botmoduleproject1.modules.pm4_risk_gate.capital.persistence import CapitalPersistence
from botmoduleproject1.modules.pm4_risk_gate.capital.portfolio import (
    concentration_after,
    currency_after,
    heat_after,
    heat_before,
    heat_headroom,
)
from botmoduleproject1.modules.pm4_risk_gate.capital.safe_halt import SafeHaltController
from botmoduleproject1.modules.pm4_risk_gate.capital.sizing import SizingError, size_position, stop_distance
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm8_persistence.money import MoneyError, canonical

_ZERO = Decimal("0")
_APPROVED = {CapitalDecisionState.APPROVED, CapitalDecisionState.APPROVED_REDUCED_SIZE}

_BLOCK_MAP = (
    ("global_safe_halt", CapitalDecisionState.BLOCKED_SYSTEM),
    ("system_control_state", CapitalDecisionState.BLOCKED_SYSTEM),
    ("persistence_availability", CapitalDecisionState.BLOCKED_SYSTEM),
    ("reconciliation_status", CapitalDecisionState.BLOCKED_RECONCILIATION),
    ("account_freshness", CapitalDecisionState.BLOCKED_ACCOUNT),
    ("portfolio_freshness", CapitalDecisionState.BLOCKED_DATA),
    ("market_freshness", CapitalDecisionState.BLOCKED_DATA),
    ("model_availability", CapitalDecisionState.BLOCKED_MODEL),
    ("model_freshness", CapitalDecisionState.BLOCKED_MODEL),
    ("model_quality", CapitalDecisionState.BLOCKED_MODEL),
    ("model_uncertainty", CapitalDecisionState.BLOCKED_MODEL),
    ("equity_drawdown_limit", CapitalDecisionState.BLOCKED_DRAWDOWN),
    ("daily_loss_limit", CapitalDecisionState.BLOCKED_DRAWDOWN),
    ("consecutive_loss", CapitalDecisionState.BLOCKED_DRAWDOWN),
    ("portfolio_heat", CapitalDecisionState.BLOCKED_PORTFOLIO_HEAT),
    ("symbol_exposure", CapitalDecisionState.BLOCKED_EXPOSURE),
    ("currency_exposure", CapitalDecisionState.BLOCKED_EXPOSURE),
    ("directional_exposure", CapitalDecisionState.BLOCKED_EXPOSURE),
    ("open_order_exposure", CapitalDecisionState.BLOCKED_EXPOSURE),
    ("pending_order_exposure", CapitalDecisionState.BLOCKED_EXPOSURE),
    ("correlation_concentration", CapitalDecisionState.BLOCKED_CONCENTRATION),
    ("strategy_concentration", CapitalDecisionState.BLOCKED_CONCENTRATION),
    ("profile_allocation", CapitalDecisionState.BLOCKED_CONCENTRATION),
    ("spread_limit", CapitalDecisionState.BLOCKED_SPREAD),
    ("slippage_limit", CapitalDecisionState.BLOCKED_SLIPPAGE),
)


class CapitalEvaluationService:
    def __init__(
        self,
        config: Pm4RiskGateConfig,
        *,
        clock: Any,
        persistence: Any | None = None,
        require_persistence: bool = False,
    ) -> None:
        self.config = config
        self.clock = clock
        self.metrics = CapitalMetrics()
        self.halt = SafeHaltController()
        self.store = CapitalPersistence(persistence)
        self.require_persistence = require_persistence
        self.ledger = DrawdownLedger(persistence)
        self.inject_fault: str | None = None
        self._lock = Lock()
        self._seen: dict[str, tuple[str, CapitalEvaluationResult]] = {}

    def _fault(self, point: str) -> None:
        if self.inject_fault == point:
            raise RuntimeError(f"injected fault:{point}")

    def _now(self) -> datetime:
        return ensure_aware_utc(self.clock.now(), "now")

    def evaluate(self, request: RiskEvaluationRequest) -> CapitalEvaluationResult:
        started = self.metrics.start()
        try:
            result = self._evaluate(request, persist=True, use_memo=True)
        except MoneyError as exc:
            result = self._fail_closed(request, f"non-finite money: {exc}")
        except ValueError as exc:
            if "idempotency conflict" in str(exc):
                raise
            result = self._fail_closed(request, f"evaluation exception: {exc}")
        except Exception as exc:
            result = self._fail_closed(request, f"evaluation exception: {exc}")
        self.metrics.observe(
            state=result.decision.final_decision.value,
            failed=result.decision.failed_checks,
            started=started,
        )
        return result

    def replay(self, result: CapitalEvaluationResult, request: RiskEvaluationRequest) -> CapitalEvaluationResult:
        replayed = self._evaluate(request, persist=False, use_memo=False)
        match = replayed.decision.output_hash == result.decision.output_hash
        if not match:
            self.store.divergence(
                result.decision.decision_id,
                result.decision.output_hash,
                replayed.decision.output_hash,
            )
            return CapitalEvaluationResult(
                decision=result.decision.model_copy(
                    update={"decision_status": CapitalDecisionState.REPLAY_DIVERGENCE}
                ),
                executable_intent=None,
                rejection=result.rejection,
                replay_match=False,
            )
        return result.model_copy(update={"replay_match": True})

    def _evaluate(
        self,
        request: RiskEvaluationRequest,
        *,
        persist: bool,
        use_memo: bool,
    ) -> CapitalEvaluationResult:
        now = self._now()
        input_hash = canonical_hash(request.model_dump(mode="json"))
        with self._lock:
            if use_memo:
                cached = self._seen.get(request.idempotency_key)
                if cached is not None:
                    stored_hash, stored = cached
                    if stored_hash != input_hash:
                        raise ValueError("idempotency conflict: same key with different payload")
                    return stored
                stored = self.store.lookup(request.idempotency_key, input_hash)
                if stored is not None:
                    self._seen[request.idempotency_key] = (input_hash, stored)
                    return stored

            self._fault("before_policy")
            policy_hash = canonical_hash(self.config.model_dump(mode="json"))
            self._fault("after_policy")
            self._fault("during_account")
            self._fault("during_portfolio")
            self._fault("during_model")

            persistence_ok = request.persistence_available
            if self.require_persistence and self.store.api is None:
                persistence_ok = False
            if self.store.api is not None:
                try:
                    self.store.api.health()
                except Exception:
                    persistence_ok = False

            self.ledger.observe(
                equity=request.account_equity if request.account_equity > 0 else _ZERO,
                peak=request.peak_equity,
                realized_day=request.realized_pnl_day,
                streak=request.losing_streak,
                now=now,
                persist=persist,
            )
            merged_peak = self.ledger.peak_equity or request.peak_equity
            merged_day = min(request.realized_pnl_day, -self.ledger.daily_loss)
            merged_streak = max(request.losing_streak, self.ledger.losing_streak)
            effective = request.model_copy(
                update={
                    "peak_equity": merged_peak,
                    "realized_pnl_day": merged_day,
                    "losing_streak": merged_streak,
                }
            )

            sizing = None
            sizing_error = None
            projected = _ZERO
            self._fault("during_sizing")
            try:
                headroom = (
                    heat_headroom(effective, self.config)
                    if effective.account_equity > 0 and not effective.exposure_unknown
                    else _ZERO
                )
                remaining = (
                    effective.account_equity * self.config.max_per_trade_risk_pct
                    if effective.account_equity > 0
                    else _ZERO
                )
                sizing = size_position(
                    effective,
                    self.config,
                    heat_headroom=headroom,
                    remaining_trade_budget=remaining,
                )
                projected = sizing.final_risk
            except (SizingError, ValueError, MoneyError) as exc:
                sizing_error = str(exc)

            self._fault("during_heat")
            checks = run_checks(
                effective,
                self.config,
                now=now,
                halt=self.halt.halted,
                persistence_ok=persistence_ok,
                projected_risk=projected if sizing is not None else None,
                sizing_error=sizing_error,
            )
            failed = tuple(
                c.name for c in checks if c.status in {CheckStatus.FAIL, CheckStatus.BLOCK} and c.blocking
            )
            state = _state_from(checks, sizing, effective)
            if state is CapitalDecisionState.ERROR_FAIL_CLOSED:
                approved_qty = _ZERO
                projected = _ZERO
            elif state in _APPROVED:
                approved_qty = sizing.rounded_size if sizing is not None else _ZERO
                if approved_qty <= 0:
                    state = CapitalDecisionState.REJECTED
                    failed = failed + ("position_size_validity",)
            else:
                approved_qty = _ZERO

            if state in {CapitalDecisionState.BLOCKED_DRAWDOWN, CapitalDecisionState.BLOCKED_SYSTEM}:
                self.halt.trip(state.value)

            try:
                hb = heat_before(effective) if effective.account_equity > 0 else _ZERO
                ha = heat_after(effective, projected) if effective.account_equity > 0 else _ZERO
                cb = effective.currency_exposure
                ca = currency_after(effective, projected)
                kb = effective.correlated_exposure
                ka = concentration_after(effective, projected)
            except Exception:
                hb = ha = cb = ca = kb = ka = _ZERO
                if state in _APPROVED:
                    state = CapitalDecisionState.ERROR_FAIL_CLOSED
                    approved_qty = _ZERO

            stop = _ZERO
            try:
                stop = stop_distance(effective)
            except Exception:
                stop = _ZERO
            equity = effective.account_equity if effective.account_equity > 0 else Decimal("1")

            reasons = tuple(c.reason for c in checks if c.name in failed)
            decision_id = str(uuid4())
            expires = now + timedelta(seconds=self.config.verdict_ttl_seconds)
            body = {
                "state": state.value,
                "approved_quantity": canonical(approved_qty),
                "projected_risk": canonical(projected),
                "failed": list(failed),
                "input_hash": input_hash,
                "policy_hash": policy_hash,
                "check_status": [(c.name, c.status.value, c.measured) for c in checks],
            }
            output_hash = canonical_hash(body)
            persist_ref = None
            audit_ref = f"audit:{decision_id}"

            decision = RiskDecision(
                decision_id=decision_id,
                decision_status=state,
                decision_timestamp=now,
                expires_at=expires,
                correlation_id=effective.correlation_id,
                causation_id=effective.causation_id,
                trade_intent_id=effective.trade_intent_id,
                strategy_id=effective.strategy_id,
                strategy_version=effective.strategy_version,
                profile_id=effective.profile_id,
                profile_version=effective.profile_version,
                symbol=effective.symbol,
                side=effective.side,
                requested_quantity=effective.requested_quantity,
                approved_quantity=approved_qty,
                entry_price=effective.entry_price,
                stop_loss_price=effective.stop_loss_price,
                take_profit_price=effective.take_profit_price,
                stop_distance=stop,
                monetary_risk=projected if state in _APPROVED else _ZERO,
                risk_percent_of_equity=(projected / equity) if state in _APPROVED else _ZERO,
                portfolio_heat_before=hb,
                portfolio_heat_after=ha if state in _APPROVED else hb,
                currency_exposure_before=cb,
                currency_exposure_after=ca if state in _APPROVED else cb,
                concentration_before=kb,
                concentration_after=ka if state in _APPROVED else kb,
                spread=effective.spread,
                slippage_estimate=effective.estimated_slippage,
                expected_cost=effective.estimated_commission + effective.estimated_swap,
                model_quality_status=effective.model_quality_status,
                regime_status=effective.regime,
                session_status=effective.session,
                account_status="unknown" if effective.account_unknown else "fresh",
                final_decision=state,
                decision_reasons=reasons or (state.value,),
                failed_checks=failed,
                warnings=tuple(c.name for c in checks if c.status is CheckStatus.FAIL and not c.blocking),
                policy_version=self.config.policy_version,
                policy_id=self.config.policy_id,
                configuration_hash=policy_hash,
                input_hash=input_hash,
                output_hash=output_hash,
                audit_reference=audit_ref,
                persistence_reference=persist_ref,
                checks=tuple(checks),
                sizing=sizing,
                execution_permitted=False,
                trading_readiness=False,
            )
            executable = None
            rejection = None
            if state in _APPROVED:
                executable = RiskApprovedExecutableIntent(
                    executable_intent_id=str(uuid4()),
                    risk_decision_id=decision_id,
                    trade_intent_id=effective.trade_intent_id,
                    symbol=effective.symbol,
                    side=effective.side,
                    approved_quantity=approved_qty,
                    entry_price=effective.entry_price,
                    stop_loss_price=effective.stop_loss_price,
                    take_profit_price=effective.take_profit_price,
                    maximum_slippage=effective.estimated_slippage,
                    expires_at=expires,
                    strategy_id=effective.strategy_id,
                    profile_id=effective.profile_id,
                    correlation_id=effective.correlation_id,
                    risk_policy_version=effective.risk_policy_version,
                    execution_policy_version=effective.execution_policy_version,
                    execution_allowed=False,
                    audit_reference=audit_ref,
                    persistence_reference=audit_ref,
                    creates_order=False,
                )
            else:
                rejection = RiskRejection(
                    rejection_id=str(uuid4()),
                    trade_intent_id=effective.trade_intent_id,
                    rejection_code=state.value,
                    rejection_category=state.value,
                    severity="critical" if state is CapitalDecisionState.ERROR_FAIL_CLOSED else "high",
                    explanation="; ".join(decision.decision_reasons),
                    failed_measurements=failed,
                    applicable_limits=tuple(c.limit for c in checks if c.limit),
                    policy_version=self.config.policy_version,
                    timestamp=now,
                    correlation_id=effective.correlation_id,
                    persistence_reference=persist_ref,
                )
            result = CapitalEvaluationResult(
                decision=decision, executable_intent=executable, rejection=rejection
            )
            if persist:
                self._fault("before_persist")
                try:
                    self._fault("after_decision_before_audit")
                    persist_ref = self.store.commit(
                        request=effective,
                        decision_id=decision_id,
                        input_hash=input_hash,
                        output_hash=output_hash,
                        payload=body,
                        result=result,
                    )
                    self._fault("after_audit_before_outbox")
                    self._fault("after_commit")
                    decision = decision.model_copy(update={"persistence_reference": persist_ref})
                    if executable is not None:
                        executable = executable.model_copy(update={"persistence_reference": persist_ref})
                    if rejection is not None:
                        rejection = rejection.model_copy(update={"persistence_reference": persist_ref})
                    result = CapitalEvaluationResult(
                        decision=decision, executable_intent=executable, rejection=rejection
                    )
                except ValueError as exc:
                    if "idempotency conflict" in str(exc):
                        raise
                    state = CapitalDecisionState.ERROR_FAIL_CLOSED
                    result = self._fail_closed(effective, f"persist:{exc}")
                except Exception as exc:
                    result = self._fail_closed(effective, f"persist:{exc}")
            if self.require_persistence and persist and result.decision.persistence_reference is None:
                if result.decision.final_decision in _APPROVED:
                    result = self._fail_closed(effective, "persistence reference missing")

            if use_memo:
                self._seen[request.idempotency_key] = (input_hash, result)
            return result

    def _fail_closed(self, request: RiskEvaluationRequest, reason: str) -> CapitalEvaluationResult:
        now = self._now()
        decision_id = str(uuid4())
        checks = tuple(
            CheckOutcome(
                name=name,
                status=CheckStatus.BLOCK,
                reason=reason,
                policy_version=self.config.policy_version,
                blocking=True,
                severity="critical",
            )
            for name in CHECK_CATALOG
        )
        decision = RiskDecision(
            decision_id=decision_id,
            decision_status=CapitalDecisionState.ERROR_FAIL_CLOSED,
            decision_timestamp=now,
            expires_at=now + timedelta(seconds=self.config.verdict_ttl_seconds),
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            trade_intent_id=request.trade_intent_id,
            strategy_id=request.strategy_id,
            strategy_version=request.strategy_version,
            profile_id=request.profile_id,
            profile_version=request.profile_version,
            symbol=request.symbol,
            side=request.side,
            requested_quantity=request.requested_quantity,
            approved_quantity=_ZERO,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            take_profit_price=request.take_profit_price,
            stop_distance=_ZERO,
            monetary_risk=_ZERO,
            risk_percent_of_equity=_ZERO,
            portfolio_heat_before=_ZERO,
            portfolio_heat_after=_ZERO,
            currency_exposure_before=_ZERO,
            currency_exposure_after=_ZERO,
            concentration_before=_ZERO,
            concentration_after=_ZERO,
            spread=request.spread,
            slippage_estimate=request.estimated_slippage,
            expected_cost=_ZERO,
            model_quality_status=request.model_quality_status,
            regime_status=request.regime,
            session_status=request.session,
            account_status="fail_closed",
            final_decision=CapitalDecisionState.ERROR_FAIL_CLOSED,
            decision_reasons=(reason,),
            failed_checks=("global_safe_halt",),
            policy_version=self.config.policy_version,
            policy_id=self.config.policy_id,
            configuration_hash=canonical_hash(self.config.model_dump(mode="json")),
            input_hash=canonical_hash({"fail": reason}),
            output_hash=canonical_hash({"state": "ERROR_FAIL_CLOSED", "reason": reason}),
            audit_reference=f"audit:{decision_id}",
            persistence_reference=None,
            checks=checks,
            execution_permitted=False,
            trading_readiness=False,
        )
        rejection = RiskRejection(
            rejection_id=str(uuid4()),
            trade_intent_id=request.trade_intent_id,
            rejection_code=CapitalDecisionState.ERROR_FAIL_CLOSED.value,
            rejection_category="fail_closed",
            severity="critical",
            explanation=reason,
            policy_version=self.config.policy_version,
            timestamp=now,
            correlation_id=request.correlation_id,
        )
        return CapitalEvaluationResult(decision=decision, rejection=rejection)


def _state_from(checks: list[CheckOutcome], sizing, request: RiskEvaluationRequest) -> CapitalDecisionState:
    blocking = {c.name: c for c in checks if c.blocking and c.status in {CheckStatus.FAIL, CheckStatus.BLOCK}}
    for name, state in _BLOCK_MAP:
        if name in blocking:
            return state
    if "cooldown" in blocking and len(blocking) == 1:
        return CapitalDecisionState.DEFERRED
    if blocking:
        return CapitalDecisionState.REJECTED
    if sizing is None or sizing.rounded_size <= 0:
        return CapitalDecisionState.REJECTED
    if sizing.rounded_size < request.requested_quantity:
        return CapitalDecisionState.APPROVED_REDUCED_SIZE
    return CapitalDecisionState.APPROVED
