#!/usr/bin/env python3
"""
Experiment runner for orchestrating test generation, evaluation, and aggregation.

This module coordinates the execution of experiment phases, integrating with
existing generation and evaluation scripts.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from impl.scripts.experiment_config import ExperimentConfig
from impl.scripts.experiment_logger import ExperimentLogger, ProgressBar
from impl.scripts.result_manager import ResultManager
from impl.scripts.test_run_utils import get_run_id_from_path


class ExperimentRunner:
    """
    Orchestrates experiment execution phases.
    
    Coordinates:
    - Test generation (single/collab/competitive)
    - Test execution (pytest)
    - Evaluation (coverage/diversity)
    - Result aggregation
    """
    
    def __init__(
        self,
        config: ExperimentConfig,
        logger: ExperimentLogger,
        result_manager: ResultManager,
    ):
        """
        Initialize experiment runner.
        
        Args:
            config: Experiment configuration
            logger: Experiment logger
            result_manager: Result manager
        """
        self.config = config
        self.logger = logger
        self.result_manager = result_manager
        
        # Get script directory
        self.script_dir = Path(__file__).parent
        self.impl_dir = self.script_dir.parent
        
        # Track generation results
        self.generation_results: Dict[str, Path] = {}
        
        # Track evaluation results
        self.evaluation_results: Dict[str, Dict[str, Path]] = {}
    
    def validate_prerequisites(self) -> List[str]:
        """
        Validate prerequisites for experiment execution.
        
        Returns:
            List of error messages (empty if all prerequisites met)
        """
        errors = []
        
        # Check LLM availability
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_ollama = False
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            has_ollama = response.status_code == 200
        except Exception:
            pass
        
        if not has_openai and not has_ollama:
            errors.append("No LLM service available. Please start Ollama or set OPENAI_API_KEY")
        
        # Check CUT module exists
        cut_module_path = self.impl_dir / "cut" / f"{self.config.cut_module}.py"
        if not cut_module_path.exists():
            errors.append(f"CUT module not found: {cut_module_path}")
        
        # Check required scripts exist
        required_scripts = [
            "generate_single.py",
            "generate_collab.py",
            "generate_competitive.py",
            "run_pytest.py",
            "eval_coverage.py",
            "eval_diversity.py",
            "aggregate.py",
        ]
        for script_name in required_scripts:
            script_path = self.script_dir / script_name
            if not script_path.exists():
                errors.append(f"Required script not found: {script_path}")
        
        return errors
    
    def run_generation_phase(self) -> Dict[str, Path]:
        """
        Execute test generation for all enabled modes.
        
        Returns:
            Dictionary mapping mode names to test directory paths
        """
        self.logger.phase_start("Generation", f"CUT module: {self.config.cut_module}")
        
        results = {}
        
        # Single-agent generation
        if self.config.generation.single.get("enabled"):
            try:
                test_dir = self._run_single_generation()
                results["single"] = test_dir
                self.generation_results["single"] = test_dir
            except Exception as e:
                self.logger.error(f"Single-agent generation failed: {e}")
                raise
        
        # Collaborative generation
        if self.config.generation.collab.get("enabled"):
            try:
                test_dir = self._run_collab_generation()
                results["collab"] = test_dir
                self.generation_results["collab"] = test_dir
            except Exception as e:
                self.logger.error(f"Collaborative generation failed: {e}")
                raise
        
        # Competitive generation
        if self.config.generation.competitive.get("enabled"):
            try:
                test_dir = self._run_competitive_generation()
                results["competitive"] = test_dir
                self.generation_results["competitive"] = test_dir
            except Exception as e:
                self.logger.error(f"Competitive generation failed: {e}")
                raise
        
        # Save generation results
        for mode, test_dir in results.items():
            run_id = get_run_id_from_path(test_dir)
            self.result_manager.save_generation_result(mode, test_dir, run_id)
        
        self.logger.phase_end("Generation", f"Generated tests for {len(results)} mode(s)")
        
        return results
    
    def _run_single_generation(self) -> Path:
        """Run single-agent test generation."""
        self.logger.info("Running single-agent test generation...")
        
        num_tests = self.config.generation.single.get("num_tests", self.config.num_tests)
        
        cmd = [
            sys.executable,
            str(self.script_dir / "generate_single.py"),
            "--cut-module", self.config.cut_module,
            "--num-tests", str(num_tests),
        ]
        
        # Set PYTHONPATH so scripts can import impl module
        env = os.environ.copy()
        pythonpath = str(self.impl_dir.parent)
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = pythonpath
        
        result = subprocess.run(
            cmd,
            cwd=self.impl_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            self.logger.error(f"Generation failed:\n{result.stderr}")
            raise RuntimeError(f"Single-agent generation failed: {result.stderr}")
        
        # Find the generated test directory
        test_dir = self._find_latest_test_dir("single")
        self.logger.success(f"Single-agent generation completed: {test_dir}")
        
        return test_dir
    
    def _run_collab_generation(self) -> Path:
        """Run collaborative test generation."""
        self.logger.info("Running collaborative test generation...")
        
        num_agents = self.config.generation.collab.get("num_agents", 3)
        num_tests = self.config.generation.collab.get("num_tests", self.config.num_tests)
        
        cmd = [
            sys.executable,
            str(self.script_dir / "generate_collab.py"),
            "--cut-module", self.config.cut_module,
            "--num-agents", str(num_agents),
            "--num-tests", str(num_tests),
        ]
        
        # Set PYTHONPATH so scripts can import impl module
        env = os.environ.copy()
        pythonpath = str(self.impl_dir.parent)
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = pythonpath
        
        result = subprocess.run(
            cmd,
            cwd=self.impl_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            self.logger.error(f"Generation failed:\n{result.stderr}")
            raise RuntimeError(f"Collaborative generation failed: {result.stderr}")
        
        # Find the generated test directory
        test_dir = self._find_latest_test_dir("collab")
        self.logger.success(f"Collaborative generation completed: {test_dir}")
        
        return test_dir
    
    def _run_competitive_generation(self) -> Path:
        """Run competitive test generation."""
        self.logger.info("Running competitive test generation...")
        
        num_agents = self.config.generation.competitive.get("num_agents", 2)
        num_tests = self.config.generation.competitive.get("num_tests", self.config.num_tests)
        competition_mode = self.config.generation.competitive.get("competition_mode", "adversarial")
        
        cmd = [
            sys.executable,
            str(self.script_dir / "generate_competitive.py"),
            "--cut-module", self.config.cut_module,
            "--num-agents", str(num_agents),
            "--num-tests", str(num_tests),
            "--competition-mode", competition_mode,
        ]
        
        # Set PYTHONPATH so scripts can import impl module
        env = os.environ.copy()
        pythonpath = str(self.impl_dir.parent)
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = pythonpath
        
        result = subprocess.run(
            cmd,
            cwd=self.impl_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            self.logger.error(f"Generation failed:\n{result.stderr}")
            raise RuntimeError(f"Competitive generation failed: {result.stderr}")
        
        # Find the generated test directory
        test_dir = self._find_latest_test_dir("competitive")
        self.logger.success(f"Competitive generation completed: {test_dir}")
        
        return test_dir
    
    def _find_latest_test_dir(self, mode: str) -> Path:
        """
        Find the most recent test directory for a mode.
        
        Args:
            mode: Generation mode (single/collab/competitive)
        
        Returns:
            Path to most recent test directory
        """
        tests_generated_dir = self.impl_dir / "tests_generated" / mode
        
        if not tests_generated_dir.exists():
            raise FileNotFoundError(f"Test directory not found: {tests_generated_dir}")
        
        # Find timestamped subdirectories
        timestamped_dirs = [
            d for d in tests_generated_dir.iterdir()
            if d.is_dir() and d.name.count("_") == 1  # Format: YYYYMMDD_HHMMSS
        ]
        
        if timestamped_dirs:
            # Sort by modification time, get most recent
            latest_dir = max(timestamped_dirs, key=lambda d: d.stat().st_mtime)
            return latest_dir
        
        # Fallback to mode directory itself
        return tests_generated_dir
    
    def run_evaluation_phase(self) -> Dict[str, Dict[str, Path]]:
        """
        Execute all enabled evaluations.
        
        Returns:
            Dictionary mapping metric types to mode-to-result-file mappings
        """
        self.logger.phase_start("Evaluation")
        
        results = {}
        
        # Run pytest if enabled
        if self.config.evaluation.pytest.get("enabled"):
            self._run_pytest_evaluation()
        
        # Run coverage evaluation
        if self.config.evaluation.coverage.get("enabled"):
            coverage_results = self._run_coverage_evaluation()
            results["coverage"] = coverage_results
            self.evaluation_results["coverage"] = coverage_results
        
        # Run diversity analysis
        if self.config.evaluation.diversity.get("enabled"):
            diversity_results = self._run_diversity_evaluation()
            results["diversity"] = diversity_results
            self.evaluation_results["diversity"] = diversity_results
        
        # Save evaluation results
        for metric_type, mode_results in results.items():
            for mode, result_file in mode_results.items():
                metrics = None
                if result_file.exists():
                    try:
                        import json
                        with open(result_file, 'r') as f:
                            metrics = json.load(f)
                    except Exception:
                        pass
                self.result_manager.save_evaluation_result(metric_type, mode, result_file, metrics)
        
        self.logger.phase_end("Evaluation", f"Completed {len(results)} evaluation type(s)")
        
        return results
    
    def _run_pytest_evaluation(self) -> None:
        """Run pytest on generated tests."""
        self.logger.info("Running pytest evaluation...")
        
        verbose = self.config.evaluation.pytest.get("verbose", False)
        
        for mode, test_dir in self.generation_results.items():
            self.logger.info(f"Running pytest for {mode} mode...")
            
            cmd = [
                sys.executable,
                str(self.script_dir / "run_pytest.py"),
                "--test-dir", str(test_dir),
                "--cut-module-path", str(self.impl_dir / "cut"),
            ]
            
            if verbose:
                cmd.append("--verbose")
            
            # Set PYTHONPATH so scripts can import impl module
            env = os.environ.copy()
            pythonpath = str(self.impl_dir.parent)
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = pythonpath
            
            result = subprocess.run(
                cmd,
                cwd=self.impl_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            
            # pytest returns non-zero if tests fail, but that's OK
            if result.returncode == 0:
                self.logger.success(f"Pytest passed for {mode} mode")
            else:
                self.logger.warning(f"Some tests failed for {mode} mode (this is OK)")
    
    def _run_coverage_evaluation(self) -> Dict[str, Path]:
        """Run coverage evaluation."""
        self.logger.info("Running coverage evaluation...")
        
        report_format = self.config.evaluation.coverage.get("report_format", "json")
        results = {}
        
        for mode, test_dir in self.generation_results.items():
            self.logger.info(f"Evaluating coverage for {mode} mode...")
            
            result_file = self.result_manager.metrics_dir / f"coverage_{self.config.cut_module}_{mode}.json"
            
            cmd = [
                sys.executable,
                str(self.script_dir / "eval_coverage.py"),
                "--test-dir", str(test_dir),
                "--cut-module", self.config.cut_module,
                "--output-file", str(result_file),
                "--report-format", report_format,
            ]
            
            # Set PYTHONPATH so scripts can import impl module
            env = os.environ.copy()
            pythonpath = str(self.impl_dir.parent)
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = pythonpath
            
            result = subprocess.run(
                cmd,
                cwd=self.impl_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                self.logger.success(f"Coverage evaluation completed for {mode} mode")
                results[mode] = result_file
            else:
                self.logger.warning(f"Coverage evaluation failed for {mode} mode: {result.stderr}")
                # Still record the result file path even if evaluation failed
                results[mode] = result_file
        
        return results
    
    def _run_diversity_evaluation(self) -> Dict[str, Path]:
        """Run diversity analysis."""
        self.logger.info("Running diversity analysis...")
        
        metric = self.config.evaluation.diversity.get("metric", "syntactic")
        results = {}
        
        for mode, test_dir in self.generation_results.items():
            self.logger.info(f"Evaluating diversity for {mode} mode...")
            
            result_file = self.result_manager.metrics_dir / f"diversity_{self.config.cut_module}_{mode}.json"
            
            cmd = [
                sys.executable,
                str(self.script_dir / "eval_diversity.py"),
                "--test-dir", str(test_dir),
                "--output-file", str(result_file),
                "--diversity-metric", metric,
            ]
            
            # Set PYTHONPATH so scripts can import impl module
            env = os.environ.copy()
            pythonpath = str(self.impl_dir.parent)
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = pythonpath
            
            result = subprocess.run(
                cmd,
                cwd=self.impl_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                self.logger.success(f"Diversity analysis completed for {mode} mode")
                results[mode] = result_file
            else:
                self.logger.warning(f"Diversity analysis failed for {mode} mode: {result.stderr}")
                results[mode] = result_file
        
        return results
    
    def run_aggregation_phase(self) -> List[Path]:
        """
        Aggregate evaluation results.
        
        Returns:
            List of paths to aggregated result files
        """
        if not self.config.aggregation.get("enabled", True):
            self.logger.info("Aggregation disabled, skipping...")
            return []
        
        self.logger.phase_start("Aggregation")
        
        formats = self.config.aggregation.get("formats", ["csv", "html"])
        results = []
        
        # Use the metrics directory as results directory for aggregation
        results_dir = self.result_manager.metrics_dir
        
        for fmt in formats:
            if fmt == "csv":
                output_file = self.result_manager.reports_dir / "results_summary.csv"
            elif fmt == "html":
                output_file = self.result_manager.reports_dir / "results_summary.html"
            elif fmt == "json":
                output_file = self.result_manager.reports_dir / "results_summary.json"
            else:
                self.logger.warning(f"Unknown aggregation format: {fmt}")
                continue
            
            self.logger.info(f"Aggregating results in {fmt} format...")
            
            cmd = [
                sys.executable,
                str(self.script_dir / "aggregate.py"),
                "--results-dir", str(results_dir),
                "--output-file", str(output_file),
                "--output-format", fmt,
            ]
            
            # Set PYTHONPATH so scripts can import impl module
            env = os.environ.copy()
            pythonpath = str(self.impl_dir.parent)
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = pythonpath
            
            result = subprocess.run(
                cmd,
                cwd=self.impl_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                self.logger.success(f"Aggregation completed: {output_file}")
                results.append(output_file)
            else:
                self.logger.warning(f"Aggregation failed for {fmt} format: {result.stderr}")
        
        self.logger.phase_end("Aggregation", f"Generated {len(results)} aggregated result file(s)")
        
        return results
    
    def get_experiment_status(self) -> Dict[str, Any]:
        """
        Get current experiment status.
        
        Returns:
            Dictionary with experiment status information
        """
        return {
            "experiment_id": self.result_manager.experiment_id,
            "cut_module": self.config.cut_module,
            "generation_results": {mode: str(path) for mode, path in self.generation_results.items()},
            "evaluation_results": {
                metric_type: {mode: str(path) for mode, path in mode_results.items()}
                for metric_type, mode_results in self.evaluation_results.items()
            },
            "metadata_file": str(self.result_manager.metadata_file),
        }
