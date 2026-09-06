"""Process lifecycle supervisor for the native MoScript runtime.

Owns spawn, streaming, byte-budget enforcement, timeout, signal handling,
and reaping. Returns a structured ProcessOutcome; it does not interpret
MoScript semantics.
"""
from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ProcessOutcome:
    returncode: int | None
    termination: Literal[
        "exit",
        "signal",
        "timeout",
        "output_limit",
        "cancelled",
        "spawn_error",
    ]
    signal_number: int | None = None
    signal_name: str | None = None
    stdout: bytes = b""
    stderr: bytes = b""
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    stdout_bytes_observed: int = 0
    stderr_bytes_observed: int = 0
    duration_ms: int = 0
    spawn_errno: int | None = None


class ProcessSupervisor:
    """Supervise a single native process: bounded, observable, reaped."""

    def __init__(
        self,
        *,
        execution_timeout: float = 60.0,
        max_output_bytes: int | None = 16 * 1024 * 1024,
        term_grace_seconds: float = 0.5,
    ):
        self.execution_timeout = execution_timeout
        self.max_output_bytes = max_output_bytes
        self.term_grace_seconds = term_grace_seconds

    def _signal_name(self, sig: int) -> str:
        return signal.Signals(sig).name if 1 <= sig < signal.NSIG else f"SIGNAL_{sig}"

    def _pgroup_terminate(self, pgid: int, sig: int) -> None:
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            pass

    def _wait_and_drain(
        self,
        proc: subprocess.Popen,
        sel: selectors.BaseSelector,
        deadline: float,
        collecting: bool,
    ) -> tuple[bytearray, bytearray, int, int, bool, bool]:
        """Drain remaining pipe data without retaining if collecting is False."""
        stdout = bytearray()
        stderr = bytearray()
        observed_out = 0
        observed_err = 0
        truncated_out = False
        truncated_err = False

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            ready = sel.select(timeout=max(0, remaining))
            if not ready and proc.poll() is not None:
                break

            for key, _ in ready:
                fd = key.fd
                chunk = os.read(fd, 8192)
                if not chunk:
                    sel.unregister(fd)
                    continue

                if fd == proc.stdout.fileno():
                    observed_out += len(chunk)
                    if collecting:
                        stdout.extend(chunk)
                    else:
                        truncated_out = True
                elif fd == proc.stderr.fileno():
                    observed_err += len(chunk)
                    if collecting:
                        stderr.extend(chunk)
                    else:
                        truncated_err = True

            if proc.poll() is not None:
                break

        return stdout, stderr, observed_out, observed_err, truncated_out, truncated_err

    def run(self, argv: list[str], phase: str = "") -> ProcessOutcome:
        """Run argv under the supervisor and return a ProcessOutcome."""
        start = time.monotonic()
        deadline = start + self.execution_timeout
        reason: ProcessOutcome.termination | None = None

        try:
            proc = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                close_fds=True,
            )
        except OSError as exc:
            return ProcessOutcome(
                returncode=None,
                termination="spawn_error",
                duration_ms=int((time.monotonic() - start) * 1000),
                spawn_errno=exc.errno,
            )

        pgid = os.getpgid(proc.pid)
        sel = selectors.DefaultSelector()
        sel.register(proc.stdout, selectors.EVENT_READ)
        sel.register(proc.stderr, selectors.EVENT_READ)

        stdout = bytearray()
        stderr = bytearray()
        observed_out = 0
        observed_err = 0
        total_retained = 0
        stdout_truncated = False
        stderr_truncated = False

        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    reason = "timeout"
                    self._pgroup_terminate(pgid, signal.SIGTERM)
                    break

                if proc.poll() is not None:
                    # Process has exited; drain remaining bytes.
                    break

                ready = sel.select(timeout=min(remaining, 0.05))
                for key, _ in ready:
                    fd = key.fd
                    chunk = os.read(fd, 8192)
                    if not chunk:
                        sel.unregister(fd)
                        continue

                    if fd == proc.stdout.fileno():
                        observed_out += len(chunk)
                        if self.max_output_bytes is None or total_retained + len(chunk) <= self.max_output_bytes:
                            stdout.extend(chunk)
                            if self.max_output_bytes is not None:
                                total_retained += len(chunk)
                        else:
                            room = self.max_output_bytes - total_retained
                            if room > 0:
                                stdout.extend(chunk[:room])
                                total_retained += room
                            stdout_truncated = True
                            reason = "output_limit"
                    elif fd == proc.stderr.fileno():
                        observed_err += len(chunk)
                        if self.max_output_bytes is None or total_retained + len(chunk) <= self.max_output_bytes:
                            stderr.extend(chunk)
                            if self.max_output_bytes is not None:
                                total_retained += len(chunk)
                        else:
                            room = self.max_output_bytes - total_retained
                            if room > 0:
                                stderr.extend(chunk[:room])
                                total_retained += room
                            stderr_truncated = True
                            reason = "output_limit"

                if reason == "output_limit":
                    self._pgroup_terminate(pgid, signal.SIGTERM)
                    break

        except Exception:
            reason = "cancelled"
            self._pgroup_terminate(pgid, signal.SIGKILL)

        # Grace period after SIGTERM, then escalate to SIGKILL.
        if reason in ("timeout", "output_limit"):
            term_deadline = time.monotonic() + self.term_grace_seconds
            while proc.poll() is None and time.monotonic() < term_deadline:
                pass
            if proc.poll() is None:
                self._pgroup_terminate(pgid, signal.SIGKILL)

        # Drain without retaining once the limit has been reached.
        collecting = reason is None or reason == "spawn_error"
        if not collecting:
            term_deadline = time.monotonic() + self.term_grace_seconds
            _, _, drained_out, drained_err, trunc_out, trunc_err = self._wait_and_drain(
                proc, sel, term_deadline, collecting=False
            )
            observed_out += drained_out
            observed_err += drained_err
            stdout_truncated = stdout_truncated or trunc_out
            stderr_truncated = stderr_truncated or trunc_err

        # Reap.
        try:
            if proc.poll() is None:
                proc.wait(timeout=self.execution_timeout + 2)
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            self._pgroup_terminate(pgid, signal.SIGKILL)
            try:
                returncode = proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                returncode = None

        proc.stdout.close()
        proc.stderr.close()
        sel.close()

        if returncode is None:
            return ProcessOutcome(
                returncode=None,
                termination=reason or "signal",
                signal_number=None,
                stdout=bytes(stdout),
                stderr=bytes(stderr),
                stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated,
                stdout_bytes_observed=observed_out,
                stderr_bytes_observed=observed_err,
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        if returncode < 0:
            termination: ProcessOutcome.termination = "signal"
            sig = -returncode
            return ProcessOutcome(
                returncode=returncode,
                termination=termination,
                signal_number=sig,
                signal_name=self._signal_name(sig),
                stdout=bytes(stdout),
                stderr=bytes(stderr),
                stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated,
                stdout_bytes_observed=observed_out,
                stderr_bytes_observed=observed_err,
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        return ProcessOutcome(
            returncode=returncode,
            termination=reason or "exit",
            stdout=bytes(stdout),
            stderr=bytes(stderr),
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
            stdout_bytes_observed=observed_out,
            stderr_bytes_observed=observed_err,
            duration_ms=int((time.monotonic() - start) * 1000),
        )
