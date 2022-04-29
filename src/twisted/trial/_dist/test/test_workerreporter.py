# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for L{twisted.trial._dist.workerreporter}.
"""


from unittest import TestCase

from hamcrest import assert_that, equal_to, has_length, has_properties
from hamcrest.core.matcher import Matcher

from twisted.test.iosim import connectedServerAndClient
from twisted.trial._dist.worker import LocalWorkerAMP, WorkerProtocol
from twisted.trial.reporter import TestResult
from twisted.trial.test import erroneous, pyunitcases, sample, skipping
from twisted.trial.unittest import SynchronousTestCase


def matches_result(
    successes=equal_to(0),
    errors=has_length(0),
    failures=has_length(0),
    skips=has_length(0),
    expectedFailures=has_length(0),
    unexpectedSuccesses=has_length(0),
):
    """
    Match a L{TestCase} instances with matching attributes.
    """
    return has_properties(
        {
            "successes": successes,
            "errors": errors,
            "failures": failures,
            "skips": skips,
            "expectedFailures": expectedFailures,
            "unexpectedSuccesses": unexpectedSuccesses,
        }
    )


def run(case: SynchronousTestCase, target: TestCase) -> TestResult:
    """
    Run C{target} and return a test result as populated by a worker reporter.

    @param case: A test case to use to help run the target.
    """
    result = TestResult()
    worker, local, pump = connectedServerAndClient(LocalWorkerAMP, WorkerProtocol)
    d = local.run(target, result)
    pump.pump()
    pump.pump()
    assert_that(case.successResultOf(d), equal_to({"success": True}))
    return result


class WorkerReporterTests(SynchronousTestCase):
    """
    Tests for L{WorkerReporter}.
    """

    def _check(self, target: TestCase, **expectations: Matcher) -> None:
        """
        Run the given test and assert that the result matches the given
        expectations.
        """
        assert_that(run(self, target), matches_result(**expectations))

    def test_addSuccess(self) -> None:
        """
        L{WorkerReporter} propagates successes.
        """
        self._check(sample.FooTest("test_foo"), successes=equal_to(1))

    def test_addError(self) -> None:
        """
        L{WorkerReporter} propagates errors from trial's TestCases.
        """
        self._check(
            erroneous.TestAsynchronousFail("test_exception"), errors=has_length(1)
        )

    def test_addErrorTuple(self) -> None:
        """
        L{WorkerReporter} propagates errors from pyunit's TestCases.
        """
        self._check(pyunitcases.PyUnitTest("test_error"), errors=has_length(1))

    def test_addFailure(self) -> None:
        """
        L{WorkerReporter} propagates test failures from trial's TestCases.
        """
        self._check(erroneous.TestRegularFail("test_fail"), failures=has_length(1))

    def test_addFailureTuple(self) -> None:
        """
        L{WorkerReporter} propagates test failures from pyunit's TestCases.
        """
        self._check(pyunitcases.PyUnitTest("test_fail"), failures=has_length(1))

    def test_addSkip(self) -> None:
        """
        L{WorkerReporter} propagates skips.
        """
        self._check(skipping.SynchronousSkipping("test_skip1"), skips=has_length(1))

    def test_addExpectedFailure(self) -> None:
        """
        L{WorkerReporter} propagates expected failures.
        """
        self._check(
            skipping.SynchronousStrictTodo("test_todo1"), expectedFailures=has_length(1)
        )

    def test_addUnexpectedSuccess(self) -> None:
        """
        L{WorkerReporter} propagates unexpected successes.
        """
        self._check(
            skipping.SynchronousTodo("test_todo3"), unexpectedSuccesses=has_length(1)
        )
