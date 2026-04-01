"""
Integration tests for Docker deployment.
"""
import pytest


class TestDocker:
    """Tests for Docker configuration."""

    def test_dockerfile_exists(self):
        """Verify Dockerfile exists."""
        import os
        docker_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "Dockerfile",
        )
        assert os.path.exists(docker_dir), "Dockerfile should exist"

    def test_docker_compose_exists(self):
        """Verify docker-compose.yml exists."""
        import os
        compose_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "docker-compose.yml",
        )
        assert os.path.exists(compose_path), "docker-compose.yml should exist"

    def test_prometheus_config_exists(self):
        """Verify prometheus.yml exists."""
        import os
        prom_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "prometheus.yml",
        )
        assert os.path.exists(prom_path), "prometheus.yml should exist"

    def test_dockerignore_exists(self):
        """Verify .dockerignore exists."""
        import os
        dockerignore = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            ".dockerignore",
        )
        assert os.path.exists(dockerignore), ".dockerignore should exist"

    def test_dockerfile_has_healthcheck(self):
        """Verify Dockerfile contains healthcheck."""
        import os
        dockerfile = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "Dockerfile",
        )
        with open(dockerfile) as f:
            content = f.read()
        assert "HEALTHCHECK" in content, "Dockerfile should have HEALTHCHECK"

    def test_dockerfile_uses_non_root_user(self):
        """Verify Dockerfile uses non-root user."""
        import os
        dockerfile = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "Dockerfile",
        )
        with open(dockerfile) as f:
            content = f.read()
        assert "useradd" in content or "USER" in content, \
            "Dockerfile should create and switch to non-root user"

    def test_docker_compose_has_redis_healthcheck(self):
        """Verify docker-compose has Redis healthcheck."""
        import os
        compose_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "docker-compose.yml",
        )
        with open(compose_path) as f:
            content = f.read()
        assert "healthcheck" in content.lower(), \
            "docker-compose.yml should have healthchecks"
        assert "redis" in content.lower(), "docker-compose should include redis"

    def test_docker_compose_has_prometheus(self):
        """Verify docker-compose includes Prometheus."""
        import os
        compose_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "docker-compose.yml",
        )
        with open(compose_path) as f:
            content = f.read()
        assert "prometheus" in content.lower(), \
            "docker-compose should include prometheus"

    def test_dockerfile_exposes_port_8000(self):
        """Verify Dockerfile exposes port 8000."""
        import os
        dockerfile = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "Dockerfile",
        )
        with open(dockerfile) as f:
            content = f.read()
        assert "EXPOSE 8000" in content, "Dockerfile should EXPOSE 8000"
