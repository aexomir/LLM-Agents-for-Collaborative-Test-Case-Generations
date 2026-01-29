#!/usr/bin/env python3
"""
Main experiment orchestrator CLI.

This is the entry point for running end-to-end experiments comparing
single-agent, collaborative, and competitive test generation methods.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from impl.scripts.experiment_config import (
    ExperimentConfig,
    load_config,
    get_default_config_path,
)
from impl.scripts.experiment_logger import ExperimentLogger
from impl.scripts.result_manager import ResultManager
from impl.scripts.experiment_runner import ExperimentRunner
from impl.scripts.test_run_utils import generate_run_id


def generate_experiment_id(config: ExperimentConfig) -> str:
    """
    Generate or retrieve experiment ID.
    
    Args:
        config: Experiment configuration
    
    Returns:
        Experiment ID string
    """
    # Check if ID is set in config
    experiment_id = config.experiment.get("id")
    
    if experiment_id:
        return experiment_id
    
    # Generate new ID
    timestamp_id = generate_run_id()
    cut_module = config.cut_module
    return f"{cut_module}_{timestamp_id}"


def main():
    """Main entry point for experiment orchestrator."""
    parser = argparse.ArgumentParser(
        description="Run end-to-end experiments comparing test generation methods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default config
  python scripts/run_experiments.py

  # Custom configuration file
  python scripts/run_experiments.py --config configs/custom_experiment.yaml

  # Override specific parameters
  python scripts/run_experiments.py \\
    --cut-module humaneval_subset \\
    --num-tests 20 \\
    --experiment-id exp_001

  # Verbose logging
  python scripts/run_experiments.py --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to experiment configuration file (YAML)",
    )
    parser.add_argument(
        "--cut-module",
        type=str,
        default=None,
        help="Override CUT module name",
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=None,
        help="Override number of tests to generate",
    )
    parser.add_argument(
        "--experiment-id",
        type=str,
        default=None,
        help="Override experiment ID (auto-generated if not provided)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Override logging level",
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip test generation phase (use existing tests)",
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Skip evaluation phase",
    )
    parser.add_argument(
        "--skip-aggregation",
        action="store_true",
        help="Skip aggregation phase",
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_path = args.config or get_default_config_path()
        
        if config_path.exists():
            print(f"Loading configuration from: {config_path}")
            config = load_config(config_path)
        else:
            print("Using default configuration")
            config = ExperimentConfig()
        
        # Apply CLI overrides
        if args.cut_module:
            config.cut_module = args.cut_module
        if args.num_tests:
            config.num_tests = args.num_tests
        if args.experiment_id:
            config.experiment["id"] = args.experiment_id
        if args.log_level:
            config.logging["level"] = args.log_level
        
        # Generate experiment ID
        experiment_id = generate_experiment_id(config)
        config.experiment["id"] = experiment_id
        
        # Determine output directory
        base_dir = Path(config.output.get("base_dir", "results/experiments"))
        base_dir = base_dir.resolve()
        
        # Initialize result manager
        result_manager = ResultManager(base_dir, experiment_id)
        
        # Initialize logger
        logger = ExperimentLogger(
            name="experiment",
            log_dir=result_manager.logs_dir,
            level=config.logging.get("level", "INFO"),
            file_logging=config.logging.get("file", True),
            console_logging=config.logging.get("console", True),
            format_style=config.logging.get("format", "detailed"),
        )
        
        # Save initial metadata
        result_manager.save_metadata({
            "created_at": datetime.now().isoformat(),
            "config": config.to_dict(),
            "cli_args": vars(args),
        })
        
        # Print experiment header
        logger.section(f"Experiment: {experiment_id}")
        logger.info(f"CUT Module: {config.cut_module}")
        logger.info(f"Number of Tests: {config.num_tests}")
        logger.info(f"Experiment Directory: {result_manager.get_experiment_dir()}")
        logger.info("")
        
        # Initialize experiment runner
        runner = ExperimentRunner(config, logger, result_manager)
        
        # Validate prerequisites
        logger.info("Validating prerequisites...")
        errors = runner.validate_prerequisites()
        if errors:
            logger.error("Prerequisites validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)
        logger.success("All prerequisites validated")
        logger.info("")
        
        # Run experiment phases
        try:
            # Generation phase
            if not args.skip_generation:
                generation_results = runner.run_generation_phase()
                logger.info("")
            else:
                logger.info("Skipping generation phase (--skip-generation)")
                logger.info("")
            
            # Evaluation phase
            if not args.skip_evaluation:
                evaluation_results = runner.run_evaluation_phase()
                logger.info("")
            else:
                logger.info("Skipping evaluation phase (--skip-evaluation)")
                logger.info("")
            
            # Aggregation phase
            if not args.skip_aggregation:
                aggregation_results = runner.run_aggregation_phase()
                logger.info("")
            else:
                logger.info("Skipping aggregation phase (--skip-aggregation)")
                logger.info("")
            
            # Generate experiment report
            logger.info("Generating experiment report...")
            report_path = result_manager.create_experiment_report(
                report_format="markdown",
                include_metrics=True,
            )
            logger.success(f"Experiment report generated: {report_path}")
            
            # Validate results
            logger.info("Validating results...")
            validation_errors = result_manager.validate_results()
            if validation_errors:
                logger.warning(f"Found {len(validation_errors)} validation issue(s):")
                for error in validation_errors:
                    logger.warning(f"  - {error}")
            else:
                logger.success("All results validated successfully")
            
            # Print summary
            logger.section("Experiment Complete")
            logger.info(f"Experiment ID: {experiment_id}")
            logger.info(f"Results Directory: {result_manager.get_experiment_dir()}")
            logger.info(f"Log File: {logger.get_log_file()}")
            logger.info(f"Report: {report_path}")
            
            # Print result paths
            result_paths = result_manager.get_result_paths()
            logger.info("")
            logger.info("Result Files:")
            if "generation_results" in result_paths:
                logger.info("  Generation Results:")
                for mode, path in result_paths["generation_results"].items():
                    logger.info(f"    {mode}: {path}")
            if "evaluation_results" in result_paths:
                logger.info("  Evaluation Results:")
                for metric_type, mode_results in result_paths["evaluation_results"].items():
                    logger.info(f"    {metric_type}:")
                    for mode, path in mode_results.items():
                        logger.info(f"      {mode}: {path}")
            
            logger.info("")
            logger.success("Experiment completed successfully!")
            
        except KeyboardInterrupt:
            logger.warning("Experiment interrupted by user")
            sys.exit(130)
        except Exception as e:
            logger.error(f"Experiment failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
