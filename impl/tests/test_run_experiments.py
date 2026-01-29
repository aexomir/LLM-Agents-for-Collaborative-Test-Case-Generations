#!/usr/bin/env python3
"""
Unit tests for experiment orchestration components.

Tests configuration loading, error handling, and result validation.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from impl.scripts.experiment_config import (
    ExperimentConfig,
    load_config,
    save_config,
    GenerationConfig,
    EvaluationConfig,
)
from impl.scripts.experiment_logger import ExperimentLogger
from impl.scripts.result_manager import ResultManager


class TestExperimentConfig:
    """Test experiment configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = ExperimentConfig()
        
        assert config.cut_module == "humaneval_subset"
        assert config.num_tests == 10
        assert config.generation.single["enabled"] is True
        assert config.generation.collab["enabled"] is True
        assert config.generation.competitive["enabled"] is True
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "cut_module": "test_module",
            "num_tests": 20,
            "generation": {
                "single": {"enabled": False},
            },
        }
        
        config = ExperimentConfig.from_dict(data)
        
        assert config.cut_module == "test_module"
        assert config.num_tests == 20
        assert config.generation.single["enabled"] is False
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = ExperimentConfig()
        
        # Valid config should have no errors
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid config
        config.cut_module = ""
        errors = config.validate()
        assert len(errors) > 0
        assert any("cut_module" in e for e in errors)
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = ExperimentConfig()
        config_dict = config.to_dict()
        
        assert "cut_module" in config_dict
        assert "num_tests" in config_dict
        assert "generation" in config_dict
        assert "evaluation" in config_dict
    
    def test_load_config_from_yaml(self):
        """Test loading config from YAML file."""
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "cut_module": "test_module",
                "num_tests": 15,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            config = load_config(config_path)
            assert config.cut_module == "test_module"
            assert config.num_tests == 15
        finally:
            config_path.unlink()
    
    def test_save_config(self):
        """Test saving config to YAML file."""
        config = ExperimentConfig()
        config.cut_module = "saved_module"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_config.yaml"
            save_config(config, output_path)
            
            assert output_path.exists()
            
            # Verify it can be loaded back
            loaded_config = load_config(output_path)
            assert loaded_config.cut_module == "saved_module"


class TestExperimentLogger:
    """Test experiment logging infrastructure."""
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ExperimentLogger(
                name="test",
                log_dir=Path(tmpdir),
                level="INFO",
            )
            
            assert logger.name == "test"
            assert logger.log_file is not None
    
    def test_logger_phases(self):
        """Test phase logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ExperimentLogger(
                name="test",
                log_dir=Path(tmpdir),
                level="DEBUG",
            )
            
            logger.phase_start("Generation", "Test phase")
            assert logger.current_phase == "Generation"
            
            logger.phase_end("Generation", "Complete")
            assert logger.current_phase is None
    
    def test_logger_methods(self):
        """Test logger methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ExperimentLogger(
                name="test",
                log_dir=Path(tmpdir),
                level="DEBUG",
            )
            
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.success("Success message")
            logger.failure("Failure message")
            
            # Verify log file exists and has content
            assert logger.get_log_file().exists()
            log_content = logger.get_log_file().read_text()
            assert "Debug message" in log_content
            assert "Info message" in log_content


class TestResultManager:
    """Test result management."""
    
    def test_result_manager_initialization(self):
        """Test result manager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResultManager(Path(tmpdir), "test_experiment_001")
            
            assert manager.experiment_id == "test_experiment_001"
            assert manager.experiment_dir.exists()
            assert manager.logs_dir.exists()
            assert manager.tests_dir.exists()
            assert manager.metrics_dir.exists()
            assert manager.reports_dir.exists()
    
    def test_save_metadata(self):
        """Test saving metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResultManager(Path(tmpdir), "test_experiment_001")
            
            metadata = {"test_key": "test_value"}
            manager.save_metadata(metadata)
            
            assert manager.metadata_file.exists()
            loaded_metadata = manager.load_metadata()
            assert loaded_metadata["test_key"] == "test_value"
    
    def test_save_generation_result(self):
        """Test saving generation result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResultManager(Path(tmpdir), "test_experiment_001")
            
            test_dir = Path(tmpdir) / "test_tests"
            test_dir.mkdir()
            
            result_file = manager.save_generation_result("single", test_dir, "run_001")
            
            assert result_file.exists()
            metadata = manager.load_metadata()
            assert "generation_results" in metadata
            assert "single" in metadata["generation_results"]
    
    def test_save_evaluation_result(self):
        """Test saving evaluation result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResultManager(Path(tmpdir), "test_experiment_001")
            
            result_file = Path(tmpdir) / "result.json"
            result_file.write_text(json.dumps({"score": 0.85}))
            
            saved_file = manager.save_evaluation_result(
                "coverage",
                "single",
                result_file,
                {"score": 0.85},
            )
            
            assert saved_file.exists()
            metadata = manager.load_metadata()
            assert "evaluation_results" in metadata
            assert "coverage" in metadata["evaluation_results"]
    
    def test_validate_results(self):
        """Test result validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResultManager(Path(tmpdir), "test_experiment_001")
            
            # Valid results
            test_dir = Path(tmpdir) / "test_tests"
            test_dir.mkdir()
            manager.save_generation_result("single", test_dir, "run_001")
            
            errors = manager.validate_results()
            assert len(errors) == 0
            
            # Invalid results (missing directory)
            manager.metadata["generation_results"]["invalid"] = {
                "test_dir": str(Path(tmpdir) / "nonexistent"),
            }
            manager.save_metadata()
            
            errors = manager.validate_results()
            assert len(errors) > 0
    
    def test_create_experiment_report(self):
        """Test experiment report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResultManager(Path(tmpdir), "test_experiment_001")
            
            # Add some metadata
            manager.save_metadata({
                "created_at": "2025-01-28T10:00:00",
                "config": {"cut_module": "test_module"},
            })
            
            # Generate markdown report
            report_path = manager.create_experiment_report(
                report_format="markdown",
                include_metrics=True,
            )
            
            assert report_path.exists()
            report_content = report_path.read_text()
            assert "Experiment Report" in report_content
            assert "test_experiment_001" in report_content
            
            # Generate HTML report
            html_report_path = manager.create_experiment_report(
                report_format="html",
                include_metrics=True,
            )
            
            assert html_report_path.exists()
            html_content = html_report_path.read_text()
            assert "<html>" in html_content
    
    def test_get_result_paths(self):
        """Test getting result paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResultManager(Path(tmpdir), "test_experiment_001")
            
            test_dir = Path(tmpdir) / "test_tests"
            test_dir.mkdir()
            manager.save_generation_result("single", test_dir, "run_001")
            
            paths = manager.get_result_paths()
            
            assert "experiment_dir" in paths
            assert "metadata" in paths
            assert "generation_results" in paths
            assert "single" in paths["generation_results"]


class TestIntegration:
    """Integration tests for component interaction."""
    
    def test_config_and_logger_integration(self):
        """Test config and logger integration."""
        config = ExperimentConfig()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ExperimentLogger(
                name="test",
                log_dir=Path(tmpdir),
                level=config.logging.get("level", "INFO"),
            )
            
            logger.set_phase("Generation")
            logger.info("Test message")
            
            assert logger.current_phase == "Generation"
    
    def test_result_manager_and_config_integration(self):
        """Test result manager and config integration."""
        config = ExperimentConfig()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / config.output.get("base_dir", "results/experiments")
            manager = ResultManager(base_dir, "test_experiment_001")
            
            manager.save_metadata({"config": config.to_dict()})
            
            loaded_metadata = manager.load_metadata()
            assert "config" in loaded_metadata
            assert loaded_metadata["config"]["cut_module"] == config.cut_module


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
