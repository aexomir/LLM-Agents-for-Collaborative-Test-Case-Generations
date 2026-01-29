#!/usr/bin/env python3
"""
Result management for experiment orchestration.

This module handles organized storage, validation, and report generation
for experiment results.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys


class ResultManager:
    """
    Manages experiment result storage and organization.
    
    Provides:
    - Organized directory structure
    - Metadata tracking
    - Result validation
    - Report generation
    """
    
    def __init__(self, base_dir: Path, experiment_id: str):
        """
        Initialize result manager.
        
        Args:
            base_dir: Base directory for results
            experiment_id: Unique experiment identifier
        """
        self.base_dir = Path(base_dir)
        self.experiment_id = experiment_id
        self.experiment_dir = self.base_dir / experiment_id
        
        # Create directory structure
        self.logs_dir = self.experiment_dir / "logs"
        self.tests_dir = self.experiment_dir / "tests"
        self.metrics_dir = self.experiment_dir / "metrics"
        self.reports_dir = self.experiment_dir / "reports"
        
        for dir_path in [self.logs_dir, self.tests_dir, self.metrics_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.experiment_dir / "metadata.json"
        self.metadata: Dict[str, Any] = {}
    
    def load_metadata(self) -> Dict[str, Any]:
        """
        Load experiment metadata.
        
        Returns:
            Metadata dictionary
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {}
        else:
            self.metadata = {}
        
        return self.metadata
    
    def save_metadata(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Save experiment metadata.
        
        Args:
            metadata: Optional metadata to merge with existing
        """
        if metadata:
            self.metadata.update(metadata)
        
        # Add/update timestamp
        self.metadata["last_updated"] = datetime.now().isoformat()
        self.metadata["experiment_id"] = self.experiment_id
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
    
    def save_generation_result(
        self,
        mode: str,
        test_dir: Path,
        run_id: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Save test generation result.
        
        Args:
            mode: Generation mode (single/collab/competitive)
            test_dir: Directory containing generated tests
            run_id: Optional run ID
            additional_info: Optional additional metadata
        
        Returns:
            Path to saved result metadata
        """
        result_info = {
            "mode": mode,
            "test_dir": str(test_dir),
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
        }
        
        if additional_info:
            result_info.update(additional_info)
        
        # Save to metadata
        if "generation_results" not in self.metadata:
            self.metadata["generation_results"] = {}
        self.metadata["generation_results"][mode] = result_info
        
        # Save metadata file
        self.save_metadata()
        
        # Create symlink or copy reference
        result_file = self.tests_dir / f"{mode}_generation.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_info, f, indent=2)
        
        return result_file
    
    def save_evaluation_result(
        self,
        metric_type: str,
        mode: str,
        result_file: Path,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Save evaluation result.
        
        Args:
            metric_type: Type of metric (coverage/diversity)
            mode: Generation mode (single/collab/competitive)
            result_file: Path to result JSON file
            metrics: Optional metrics dictionary
        
        Returns:
            Path to saved result reference
        """
        result_info = {
            "metric_type": metric_type,
            "mode": mode,
            "result_file": str(result_file),
            "timestamp": datetime.now().isoformat(),
        }
        
        if metrics:
            result_info["metrics"] = metrics
        
        # Save to metadata
        if "evaluation_results" not in self.metadata:
            self.metadata["evaluation_results"] = {}
        if metric_type not in self.metadata["evaluation_results"]:
            self.metadata["evaluation_results"][metric_type] = {}
        self.metadata["evaluation_results"][metric_type][mode] = result_info
        
        # Save metadata file
        self.save_metadata()
        
        # Copy result file to metrics directory
        dest_file = self.metrics_dir / f"{metric_type}_{mode}.json"
        if result_file.exists():
            import shutil
            shutil.copy2(result_file, dest_file)
        
        return dest_file
    
    def validate_results(self) -> List[str]:
        """
        Validate result files and return list of errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check metadata file exists
        if not self.metadata_file.exists():
            errors.append("Metadata file missing")
            return errors
        
        # Load metadata
        metadata = self.load_metadata()
        
        # Validate generation results
        if "generation_results" in metadata:
            for mode, result_info in metadata["generation_results"].items():
                test_dir = Path(result_info.get("test_dir", ""))
                if not test_dir.exists():
                    errors.append(f"Generation result test directory missing for {mode}: {test_dir}")
        
        # Validate evaluation results
        if "evaluation_results" in metadata:
            for metric_type, mode_results in metadata["evaluation_results"].items():
                for mode, result_info in mode_results.items():
                    result_file = Path(result_info.get("result_file", ""))
                    if not result_file.exists():
                        errors.append(f"Evaluation result file missing for {metric_type}/{mode}: {result_file}")
                    else:
                        # Validate JSON
                        try:
                            with open(result_file, 'r') as f:
                                json.load(f)
                        except json.JSONDecodeError as e:
                            errors.append(f"Invalid JSON in {metric_type}/{mode} result: {e}")
        
        return errors
    
    def get_result_paths(self) -> Dict[str, Any]:
        """
        Get paths to all result files.
        
        Returns:
            Dictionary mapping result types to paths
        """
        paths = {
            "experiment_dir": str(self.experiment_dir),
            "metadata": str(self.metadata_file),
            "logs": str(self.logs_dir),
            "tests": str(self.tests_dir),
            "metrics": str(self.metrics_dir),
            "reports": str(self.reports_dir),
        }
        
        metadata = self.load_metadata()
        
        # Add generation result paths
        if "generation_results" in metadata:
            paths["generation_results"] = {}
            for mode, result_info in metadata["generation_results"].items():
                paths["generation_results"][mode] = result_info.get("test_dir")
        
        # Add evaluation result paths
        if "evaluation_results" in metadata:
            paths["evaluation_results"] = {}
            for metric_type, mode_results in metadata["evaluation_results"].items():
                paths["evaluation_results"][metric_type] = {}
                for mode, result_info in mode_results.items():
                    paths["evaluation_results"][metric_type][mode] = result_info.get("result_file")
        
        return paths
    
    def create_experiment_report(
        self,
        report_format: str = "markdown",
        include_metrics: bool = True,
    ) -> Path:
        """
        Create experiment summary report.
        
        Args:
            report_format: Report format ('markdown' or 'html')
            include_metrics: Include detailed metrics in report
        
        Returns:
            Path to generated report file
        """
        metadata = self.load_metadata()
        
        if report_format == "markdown":
            report_path = self.reports_dir / "experiment_report.md"
            content = self._generate_markdown_report(metadata, include_metrics)
        elif report_format == "html":
            report_path = self.reports_dir / "experiment_report.html"
            content = self._generate_html_report(metadata, include_metrics)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return report_path
    
    def _generate_markdown_report(
        self,
        metadata: Dict[str, Any],
        include_metrics: bool,
    ) -> str:
        """Generate markdown report."""
        lines = []
        
        # Header
        lines.append("# Experiment Report")
        lines.append("")
        lines.append(f"**Experiment ID:** {self.experiment_id}")
        lines.append(f"**Created:** {metadata.get('created_at', 'Unknown')}")
        lines.append(f"**Last Updated:** {metadata.get('last_updated', 'Unknown')}")
        lines.append("")
        
        # Configuration
        if "config" in metadata:
            lines.append("## Configuration")
            lines.append("")
            lines.append("```yaml")
            import yaml
            lines.append(yaml.dump(metadata["config"], default_flow_style=False))
            lines.append("```")
            lines.append("")
        
        # Generation Results
        if "generation_results" in metadata:
            lines.append("## Test Generation Results")
            lines.append("")
            for mode, result_info in metadata["generation_results"].items():
                lines.append(f"### {mode.capitalize()} Mode")
                lines.append("")
                lines.append(f"- **Test Directory:** `{result_info.get('test_dir', 'N/A')}`")
                lines.append(f"- **Run ID:** {result_info.get('run_id', 'N/A')}")
                lines.append(f"- **Timestamp:** {result_info.get('timestamp', 'N/A')}")
                if "num_tests" in result_info:
                    lines.append(f"- **Tests Generated:** {result_info['num_tests']}")
                lines.append("")
        
        # Evaluation Results
        if include_metrics and "evaluation_results" in metadata:
            lines.append("## Evaluation Results")
            lines.append("")
            for metric_type, mode_results in metadata["evaluation_results"].items():
                lines.append(f"### {metric_type.capitalize()} Metrics")
                lines.append("")
                lines.append("| Mode | Result File |")
                lines.append("|------|-------------|")
                for mode, result_info in mode_results.items():
                    result_file = result_info.get("result_file", "N/A")
                    lines.append(f"| {mode} | `{result_file}` |")
                lines.append("")
        
        # Validation Status
        errors = self.validate_results()
        if errors:
            lines.append("## Validation Errors")
            lines.append("")
            for error in errors:
                lines.append(f"- ⚠️ {error}")
            lines.append("")
        else:
            lines.append("## Validation Status")
            lines.append("")
            lines.append("✓ All results validated successfully")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_html_report(
        self,
        metadata: Dict[str, Any],
        include_metrics: bool,
    ) -> str:
        """Generate HTML report."""
        html_lines = []
        
        html_lines.append("<!DOCTYPE html>")
        html_lines.append("<html>")
        html_lines.append("<head>")
        html_lines.append("<title>Experiment Report</title>")
        html_lines.append("<style>")
        html_lines.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html_lines.append("table { border-collapse: collapse; width: 100%; }")
        html_lines.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html_lines.append("th { background-color: #f2f2f2; }")
        html_lines.append("</style>")
        html_lines.append("</head>")
        html_lines.append("<body>")
        html_lines.append(f"<h1>Experiment Report</h1>")
        html_lines.append(f"<p><strong>Experiment ID:</strong> {self.experiment_id}</p>")
        html_lines.append(f"<p><strong>Created:</strong> {metadata.get('created_at', 'Unknown')}</p>")
        html_lines.append(f"<p><strong>Last Updated:</strong> {metadata.get('last_updated', 'Unknown')}</p>")
        
        # Generation Results
        if "generation_results" in metadata:
            html_lines.append("<h2>Test Generation Results</h2>")
            html_lines.append("<table>")
            html_lines.append("<tr><th>Mode</th><th>Test Directory</th><th>Run ID</th></tr>")
            for mode, result_info in metadata["generation_results"].items():
                html_lines.append(f"<tr>")
                html_lines.append(f"<td>{mode}</td>")
                html_lines.append(f"<td>{result_info.get('test_dir', 'N/A')}</td>")
                html_lines.append(f"<td>{result_info.get('run_id', 'N/A')}</td>")
                html_lines.append(f"</tr>")
            html_lines.append("</table>")
        
        # Evaluation Results
        if include_metrics and "evaluation_results" in metadata:
            html_lines.append("<h2>Evaluation Results</h2>")
            for metric_type, mode_results in metadata["evaluation_results"].items():
                html_lines.append(f"<h3>{metric_type.capitalize()}</h3>")
                html_lines.append("<table>")
                html_lines.append("<tr><th>Mode</th><th>Result File</th></tr>")
                for mode, result_info in mode_results.items():
                    html_lines.append(f"<tr>")
                    html_lines.append(f"<td>{mode}</td>")
                    html_lines.append(f"<td>{result_info.get('result_file', 'N/A')}</td>")
                    html_lines.append(f"</tr>")
                html_lines.append("</table>")
        
        html_lines.append("</body>")
        html_lines.append("</html>")
        
        return "\n".join(html_lines)
    
    def get_experiment_dir(self) -> Path:
        """Get experiment directory path."""
        return self.experiment_dir


if __name__ == "__main__":
    # Test result manager
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ResultManager(Path(tmpdir), "test_experiment_001")
        
        # Save metadata
        manager.save_metadata({
            "created_at": datetime.now().isoformat(),
            "config": {"cut_module": "test_module"},
        })
        
        # Save generation result
        test_dir = Path(tmpdir) / "test_tests"
        test_dir.mkdir()
        manager.save_generation_result("single", test_dir, "run_001")
        
        # Validate
        errors = manager.validate_results()
        print(f"Validation errors: {errors}")
        
        # Generate report
        report_path = manager.create_experiment_report()
        print(f"Report generated: {report_path}")
