DEFAULT_MAX_RUNS = 2
DEFAULT_MIN_PASSES = 1


class FlakyTestAttributes:
    """
    Attributes that will be added to flaky tests.
    """
    CURRENT_ERRORS = '_current_errors'
    CURRENT_RUNS = '_current_runs'
    CURRENT_PASSES = '_current_passes'
    MAX_RUNS = '_max_runs'
    MIN_PASSES = '_min_passes'

    def items(self):
        return (
            self.CURRENT_ERRORS,
            self.CURRENT_PASSES,
            self.CURRENT_RUNS,
            self.MAX_RUNS,
            self.MIN_PASSES,
        )

    @staticmethod
    def default_flaky_attributes(max_runs=None, min_passes=None):
        """
        Returns the default flaky attributes to set on a flaky test.

        :param max_runs: The value of the MAX_RUNS attribute to use.
        :param min_passes: The value of the MIN_PASSES attribute to use.
        :return: Dict of default flaky attributes to set on a flaky test.
        """
        if not max_runs:
            max_runs = DEFAULT_MAX_RUNS
        if not min_passes:
            min_passes = DEFAULT_MIN_PASSES
        if min_passes <= 0:
            raise ValueError('min_passes must be positive')
        if max_runs < min_passes:
            raise ValueError('min_passes is less than max_runs')

        return {
            FlakyTestAttributes.MAX_RUNS: max_runs,
            FlakyTestAttributes.MIN_PASSES: min_passes,
            FlakyTestAttributes.CURRENT_RUNS: 0,
            FlakyTestAttributes.CURRENT_PASSES: 0,
        }
