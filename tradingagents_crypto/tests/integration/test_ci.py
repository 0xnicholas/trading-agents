"""
Integration tests for CI/CD workflow.
"""
import os
import yaml
import pytest


class TestCIWorkflow:
    """Tests for GitHub Actions CI/CD workflow."""

    def test_workflow_file_exists(self):
        """Verify CI workflow file exists."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "ci.yml",
        )
        assert os.path.exists(workflow_path), "ci.yml should exist"

    def test_workflow_is_valid_yaml(self):
        """Verify CI workflow is valid YAML."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "ci.yml",
        )
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
        assert workflow is not None, "ci.yml should be valid YAML"

    def test_workflow_has_required_jobs(self):
        """Verify workflow has required jobs."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "ci.yml",
        )
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        assert "jobs" in workflow, "Workflow should have jobs"
        assert "lint" in workflow["jobs"], "Workflow should have lint job"
        assert "test" in workflow["jobs"], "Workflow should have test job"
        assert "docker" in workflow["jobs"], "Workflow should have docker job"

    def test_workflow_triggers_on_push(self):
        """Verify workflow triggers on push."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "ci.yml",
        )
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        # 'on' is a YAML keyword, may be parsed as boolean True
        triggers = workflow.get("on") or workflow.get(True) or {}
        assert "push" in triggers, "Workflow should trigger on push"

    def test_workflow_triggers_on_pull_request(self):
        """Verify workflow triggers on pull request."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "ci.yml",
        )
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        # 'on' is a YAML keyword, may be parsed as boolean True
        triggers = workflow.get("on") or workflow.get(True) or {}
        assert "pull_request" in triggers, \
            "Workflow should trigger on pull_request"

    def test_docker_job_needs_lint_and_test(self):
        """Verify docker job depends on lint and test."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "ci.yml",
        )
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        docker_job = workflow["jobs"]["docker"]
        assert "needs" in docker_job, "Docker job should have dependencies"
        assert "lint" in docker_job["needs"], "Docker should need lint"
        assert "test" in docker_job["needs"], "Docker should need test"

    def test_test_job_runs_pytest(self):
        """Verify test job runs pytest with coverage."""
        workflow_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".github",
            "workflows",
            "ci.yml",
        )
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        test_job = workflow["jobs"]["test"]
        steps = test_job.get("steps", [])

        # Find the pytest step
        pytest_step = None
        for step in steps:
            if "pytest" in step.get("run", ""):
                pytest_step = step
                break

        assert pytest_step is not None, "Test job should run pytest"
        assert "--cov=" in pytest_step["run"], "pytest should run with coverage"
