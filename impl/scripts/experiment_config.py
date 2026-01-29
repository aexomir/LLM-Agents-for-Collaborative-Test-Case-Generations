#!/usr/bin/env python3
"""
Experiment configuration management.

This module handles loading, validating, and managing experiment configurations
from YAML files with support for environment variable overrides and defaults.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import sys


@dataclass
class GenerationConfig:
    """Configuration for test generation modes."""
    single: Dict[str, Any] = field(default_factory=lambda: {"enabled": True, "num_tests": 10})
    collab: Dict[str, Any] = field(default_factory=lambda: {"enabled": True, "num_agents": 3, "num_tests": 10})
    competitive: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "num_agents": 2, "num_tests": 10, "competition_mode": "adversarial"
    })


@dataclass
class EvaluationConfig:
    """Configuration for evaluation phases."""
    pytest: Dict[str, Any] = field(default_factory=lambda: {"enabled": True, "verbose": False})
    coverage: Dict[str, Any] = field(default_factory=lambda: {"enabled": True, "report_format": "json"})
    diversity: Dict[str, Any] = field(default_factory=lambda: {"enabled": True, "metric": "syntactic"})


@dataclass
class ExperimentConfig:
    """Complete experiment configuration."""
    experiment: Dict[str, Any] = field(default_factory=lambda: {
        "id": None,
        "name": "Step 10 Experiment",
        "description": "Compare single/collab/competitive test generation"
    })
    cut_module: str = "humaneval_subset"
    num_tests: int = 10
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    aggregation: Dict[str, Any] = field(default_factory=lambda: {"enabled": True, "formats": ["csv", "html"]})
    output: Dict[str, Any] = field(default_factory=lambda: {
        "base_dir": "results/experiments",
        "create_timestamped_dirs": True
    })
    logging: Dict[str, Any] = field(default_factory=lambda: {
        "level": "INFO",
        "file": True,
        "console": True,
        "format": "detailed"
    })

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentConfig":
        """Create ExperimentConfig from dictionary."""
        config = cls()
        
        # Update experiment metadata
        if "experiment" in data:
            config.experiment.update(data["experiment"])
        
        # Update simple fields
        if "cut_module" in data:
            config.cut_module = data["cut_module"]
        if "num_tests" in data:
            config.num_tests = data["num_tests"]
        
        # Update generation config
        if "generation" in data:
            gen_data = data["generation"]
            if "single" in gen_data:
                config.generation.single.update(gen_data["single"])
            if "collab" in gen_data:
                config.generation.collab.update(gen_data["collab"])
            if "competitive" in gen_data:
                config.generation.competitive.update(gen_data["competitive"])
        
        # Update evaluation config
        if "evaluation" in data:
            eval_data = data["evaluation"]
            if "pytest" in eval_data:
                config.evaluation.pytest.update(eval_data["pytest"])
            if "coverage" in eval_data:
                config.evaluation.coverage.update(eval_data["coverage"])
            # Mutation testing removed - ignore if present in config
            if "diversity" in eval_data:
                config.evaluation.diversity.update(eval_data["diversity"])
        
        # Update aggregation
        if "aggregation" in data:
            config.aggregation.update(data["aggregation"])
        
        # Update output
        if "output" in data:
            config.output.update(data["output"])
        
        # Update logging
        if "logging" in data:
            config.logging.update(data["logging"])
        
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert ExperimentConfig to dictionary."""
        return {
            "experiment": self.experiment,
            "cut_module": self.cut_module,
            "num_tests": self.num_tests,
            "generation": {
                "single": self.generation.single,
                "collab": self.generation.collab,
                "competitive": self.generation.competitive,
            },
            "evaluation": {
                "pytest": self.evaluation.pytest,
                "coverage": self.evaluation.coverage,
                "diversity": self.evaluation.diversity,
            },
            "aggregation": self.aggregation,
            "output": self.output,
            "logging": self.logging,
        }

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors (empty if valid).
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate cut_module
        if not self.cut_module or not isinstance(self.cut_module, str):
            errors.append("cut_module must be a non-empty string")
        
        # Validate num_tests
        if not isinstance(self.num_tests, int) or self.num_tests < 1:
            errors.append("num_tests must be a positive integer")
        
        # Validate generation modes
        for mode_name, mode_config in [
            ("single", self.generation.single),
            ("collab", self.generation.collab),
            ("competitive", self.generation.competitive),
        ]:
            if not isinstance(mode_config.get("enabled"), bool):
                errors.append(f"generation.{mode_name}.enabled must be a boolean")
            if mode_config.get("enabled") and not isinstance(mode_config.get("num_tests"), int):
                errors.append(f"generation.{mode_name}.num_tests must be an integer")
        
        # Validate collab num_agents
        if self.generation.collab.get("enabled"):
            num_agents = self.generation.collab.get("num_agents")
            if not isinstance(num_agents, int) or num_agents < 1:
                errors.append("generation.collab.num_agents must be a positive integer")
        
        # Validate competitive competition_mode
        if self.generation.competitive.get("enabled"):
            mode = self.generation.competitive.get("competition_mode")
            if mode not in ["adversarial", "diversity", "coverage"]:
                errors.append("generation.competitive.competition_mode must be one of: adversarial, diversity, coverage")
        
        # Validate evaluation configs
        for eval_name, eval_config in [
            ("pytest", self.evaluation.pytest),
            ("coverage", self.evaluation.coverage),
            ("diversity", self.evaluation.diversity),
        ]:
            if not isinstance(eval_config.get("enabled"), bool):
                errors.append(f"evaluation.{eval_name}.enabled must be a boolean")
        
        # Validate diversity metric
        if self.evaluation.diversity.get("enabled"):
            metric = self.evaluation.diversity.get("metric")
            if metric not in ["syntactic", "semantic", "coverage"]:
                errors.append("evaluation.diversity.metric must be one of: syntactic, semantic, coverage")
        
        # Validate logging level
        if self.logging.get("level") not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            errors.append("logging.level must be one of: DEBUG, INFO, WARNING, ERROR")
        
        return errors


def load_config(config_path: Optional[Path] = None) -> ExperimentConfig:
    """
    Load experiment configuration from YAML file or use defaults.
    
    Args:
        config_path: Path to YAML config file. If None, uses default config.
        
    Returns:
        ExperimentConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        ValueError: If config validation fails
    """
    if config_path is None:
        # Use default config
        return ExperimentConfig()
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    if data is None:
        data = {}
    
    # Apply environment variable overrides
    data = _apply_env_overrides(data)
    
    # Create config from data
    config = ExperimentConfig.from_dict(data)
    
    # Validate
    errors = config.validate()
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return config


def _apply_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration data.
    
    Environment variables:
    - EXPERIMENT_CUT_MODULE: Override cut_module
    - EXPERIMENT_NUM_TESTS: Override num_tests
    - EXPERIMENT_ID: Override experiment.id
    
    Args:
        data: Configuration dictionary
        
    Returns:
        Updated configuration dictionary
    """
    # Override cut_module
    if "EXPERIMENT_CUT_MODULE" in os.environ:
        data["cut_module"] = os.environ["EXPERIMENT_CUT_MODULE"]
    
    # Override num_tests
    if "EXPERIMENT_NUM_TESTS" in os.environ:
        try:
            data["num_tests"] = int(os.environ["EXPERIMENT_NUM_TESTS"])
        except ValueError:
            pass  # Invalid value, ignore
    
    # Override experiment ID
    if "EXPERIMENT_ID" in os.environ:
        if "experiment" not in data:
            data["experiment"] = {}
        data["experiment"]["id"] = os.environ["EXPERIMENT_ID"]
    
    return data


def get_default_config_path() -> Path:
    """
    Get path to default configuration file.
    
    Returns:
        Path to default config file
    """
    script_dir = Path(__file__).parent
    configs_dir = script_dir / "configs"
    return configs_dir / "default_experiment.yaml"


def save_config(config: ExperimentConfig, output_path: Path) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: ExperimentConfig to save
        output_path: Path to save configuration file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False, indent=2)


if __name__ == "__main__":
    # Test configuration loading
    import argparse
    
    parser = argparse.ArgumentParser(description="Test experiment configuration")
    parser.add_argument("--config", type=Path, help="Path to config file")
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        print("Configuration loaded successfully:")
        print(yaml.dump(config.to_dict(), default_flow_style=False, sort_keys=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
