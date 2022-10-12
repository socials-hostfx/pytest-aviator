import os
import requests

from flakybot_pytest_runner.attributes import FlakyTestAttributes, DEFAULT_MIN_PASSES, DEFAULT_MAX_RUNS

AVIATOR_MARKER = "aviator"
BUILDKITE_JOB_PREFIX = "buildkite/"
CIRCLECI_JOB_PREFIX = "ci/circleci:"


class FlakybotRunner:
    runner = None
    _API_URL = "https://api.aviator.co/api/v1/flaky-tests"
    flaky_tests = {}
    min_passes = DEFAULT_MIN_PASSES
    max_runs = DEFAULT_MAX_RUNS

    def __init__(self):
        super().__init__()
        self.get_flaky_tests()

    def pytest_configure(self, config):
        """
        Perform initial configuration. Include custom markers to avoid warnings.
        https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#registering-custom-markers

        :param config: the pytest config object
        :return: None
        """
        self.runner = config.pluginmanager.getplugin("runner")

        config.addinivalue_line("markers", f"{AVIATOR_MARKER}: marks flaky tests for Flakybot to automatically rerun")

    def get_flaky_tests(self):
        """
        Get flaky test information from the Aviator API.

        :return: None
        """
        repo_name = None
        job_name = None

        # Get job and repo name
        if os.environ.get("CIRCLE_JOB"):
            # https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables
            job_name = CIRCLECI_JOB_PREFIX + os.environ.get("CIRCLE_JOB", "")
            repo_name = "{username}/{repo_name}".format(
                username=os.environ.get("CIRCLE_PROJECT_USERNAME", ""),
                repo_name=os.environ.get("CIRCLE_PROJECT_REPONAME", "")
            )
        if os.environ.get("BUILDKITE_PIPELINE_SLUG"):
            # Note: BUILDKITE_REPO is in the format "git@github.com:{repo_name}.git"
            job_name = BUILDKITE_JOB_PREFIX + os.environ.get("BUILDKITE_PIPELINE_SLUG", "")
            repo_name = os.environ.get("BUILDKITE_REPO").replace("git@github.com:", "").replace(".git", "")

        # Fetch flaky test info
        self._API_URL = os.environ.get("AVIATOR_API_URL") or self._API_URL
        API_TOKEN = os.environ.get("AVIATOR_API_TOKEN", "")
        headers = {
            "Authorization": "Bearer " + API_TOKEN,
            "Content-Type": "application/json"
        }
        params = {"repo_name": repo_name, "job_name": job_name}
        response = requests.get(self._API_URL, headers=headers, params=params).json()
        av_flaky_tests = response.get("flaky_tests", [])

        for test in av_flaky_tests:
            if test.get("test_name", ""):
                self.flaky_tests[test["test_name"]] = test

        print("flaky tests: ", self.flaky_tests)

    def pytest_runtest_protocol(self, item, nextitem):
        test_instance = self._get_test_instance(item)
        class_name = test_instance.__module__ + "." + test_instance.__name__

        print(f"test instance: {test_instance}")
        print(f"class name: {class_name}")
        print("test item: ", item.name)
        if (
            self.flaky_tests and
            self.flaky_tests.get(item.name) and
            self.flaky_tests[item.name].get("class_name") in class_name
        ):
            min_passes = self.min_passes
            max_runs = self.max_runs
            if self.flaky_tests[item.name].get("min_passes"):
                min_passes = self.flaky_tests[item.name]["min_passes"]
            if self.flaky_tests[item.name].get("max_runs"):
                max_runs = self.flaky_tests[item.name]["max_runs"]
            self._mark_flaky(item, max_runs, min_passes)
            print("item dict: ", item.__dict__.items())

    @staticmethod
    def _get_test_instance(item):
        instance = item.instance
        if not instance:
            if item.parent and item.parent.obj:
                instance = item.parent.obj
        return instance

    @classmethod
    def _get_flaky_attributes(cls, test_item):
        """
        Get all the flaky related attributes from the test.

        :param test_item: The test callable from which to get the flaky related attributes.
        :return: Dictionary containing attributes.
        """
        return {
            attr: getattr(test_item, attr, None) for attr in FlakyTestAttributes().items()
        }

    @staticmethod
    def _set_flaky_attribute(test_item, attr, value):
        """
        Sets an attribute on a flaky test.

        :param test_item: The test callable on which to set the attribute.
        :param attr: The name of the attribute.
        :param value: The value to set the attribute to.
        """
        test_item.__dict__[attr] = value

    @classmethod
    def _mark_flaky(cls, test, max_runs=None, min_passes=None):
        """
        Mark a test as flaky by setting flaky attributes.

        :param test: The given test.
        :param max_runs: The value of the FlakyTestAttributes.MAX_RUNS attribute to use.
        :param min_passes: The value of the FlakyTestAttributes.MIN_PASSES attribute to use.
        """
        attr_dict = FlakyTestAttributes.default_flaky_attributes(max_runs, min_passes)
        for attr, value in attr_dict.items():
            cls._set_flaky_attribute(test, attr, value)


PLUGIN = FlakybotRunner()
for _pytest_hook in dir(PLUGIN):
    if _pytest_hook.startswith("pytest_"):
        globals()[_pytest_hook] = getattr(PLUGIN, _pytest_hook)
