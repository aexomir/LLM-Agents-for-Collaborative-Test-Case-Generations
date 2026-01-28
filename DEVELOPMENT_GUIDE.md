# Development Guide: Step-by-Step Implementation

This guide outlines the step-by-step process for implementing the LLM-based test generation system, with branch names for each feature.

## Overview

The implementation follows this workflow:

1. **Setup** → 2. **LLM Integration** → 3. **Single-Agent Generation** → 4. **Collaborative Generation** → 5. **Competitive Generation** → 6. **Evaluation** → 7. **Integration & Testing**

---

## Step 1: Project Structure Setup

**Branch:** `chore/init`

**Status:** ✅ DONE

**What was done:**

- Created `impl/` directory structure
- Added `pyproject.toml` with dependencies (pytest, coverage, mutmut, pandas)
- Created placeholder scripts with CLI arguments
- Added `__init__.py` files for packages
- Created `impl/README.md` with usage instructions
- Added `.gitignore` for `__pycache__/` directories

**Manual steps completed:**

- ✅ Directory structure created
- ✅ Configuration files added
- ✅ Script skeletons with TODOs created

---

## Step 2: Implement LLM Abstraction Layer

**Branch:** `feature/llm-abstraction`

**Status:** ✅ DONE

**What was done:**

- Implemented `call_local_llm()` function in `impl/src/llm.py` using Ollama API
- Added support for configurable model, API URL, temperature, and max_tokens
- Added environment variable support (OLLAMA_MODEL, OLLAMA_API_URL)
- Implemented error handling for connection errors, timeouts, and API errors
- Added `requests` dependency to `pyproject.toml`
- Function supports Ollama API format with proper response parsing

**Manual steps completed:**

- ✅ Implemented `call_local_llm()` with Ollama as default backend
- ✅ Added configuration options (model, API URL, temperature, max_tokens)
- ✅ Added environment variable support for easy configuration
- ✅ Implemented comprehensive error handling
- ✅ Added requests dependency to project configuration

---

## Step 3: Implement Single-Agent Test Generation

**Branch:** `feature/single-agent-generation`

**Status:** ✅ DONE

**What was done:**

- ✅ Implemented `generate_single_tests()` in `impl/scripts/generate_single.py`
- ✅ Created dynamic CUT module loading using `importlib`
- ✅ Created prompt template in `impl/prompts/patterns/single_agent.txt`
- ✅ Implemented LLM code generation with `call_local_llm()`
- ✅ Implemented Python code extraction from LLM responses (handles code blocks)
- ✅ Implemented code validation using `ast.parse()` and test function detection
- ✅ Implemented saving generated tests to output directory
- ✅ Created sample CUT module `impl/cut/calculator.py` for testing

**Implementation details:**

- **Module Loading**: `load_cut_module()` dynamically imports modules from `impl.cut.*`
- **Source Code Extraction**: `get_module_source_code()` gets source using `inspect.getsource()`
- **Prompt Template**: Located at `impl/prompts/patterns/single_agent.txt` with `{code_under_test}` placeholder
- **Code Extraction**: `extract_python_code_from_response()` handles markdown code blocks (```python) or plain text
- **Validation**: `validate_test_code()` checks Python syntax and ensures test functions start with `test_`
- **Auto-import**: Automatically adds import statement if missing in generated code

**Manual steps completed:**

- ✅ Created prompt template directory and file
- ✅ Implemented all core functionality
- ✅ Created sample calculator module for testing
- ✅ Verified module loading and code validation logic

---

## Step 4: Implement Collaborative Test Generation

**Branch:** `feature/collaborative-generation`

**Status:** ✅ DONE

**What was done:**

- ✅ Implemented `generate_collab_tests()` in `impl/scripts/generate_collab.py`
- ✅ Created role definitions in `impl/prompts/roles/`:
  - `tester_edge_cases.txt` - Focus on edge cases and unusual scenarios
  - `tester_boundary.txt` - Focus on boundary value analysis
  - `tester_integration.txt` - Focus on integration scenarios and real-world usage
- ✅ Implemented multi-agent coordination:
  - Load role definitions from default or custom directory
  - Create prompts for each agent with their specialized role
  - Call `call_local_llm()` for each agent sequentially
  - Collect and process responses from all agents
- ✅ Implemented test merging:
  - Extract test functions from each agent's response
  - Deduplicate similar tests (by name and code similarity)
  - Combine all unique test functions into a single file
  - Validate the merged test code

**Implementation details:**

- **Role Templates**: Located in `impl/prompts/roles/` with placeholders for `{code_under_test}` and `{num_tests}`
- **Multi-Agent Coordination**: Each agent generates tests based on their specialized role (edge cases, boundary, integration)
- **Test Extraction**: Uses AST parsing to extract top-level test functions from each agent's response
- **Deduplication**: Removes duplicate test functions by name and normalized code comparison
- **Error Handling**: Continues processing if one agent fails, ensuring robustness
- **Validation**: Validates both individual agent responses and the final merged code

**Manual steps completed:**

- ✅ Created feature branch: `feature/collaborative-generation`
- ✅ Created role definition files in `impl/prompts/roles/`
- ✅ Implemented complete multi-agent coordination logic
- ✅ Implemented test merging and deduplication
- ✅ Added comprehensive error handling and logging
- ✅ Tested with validation test suite (all tests passed)
- ✅ Committed and merged to main branch

---

## Step 5: Implement Competitive Test Generation

**Branch:** `feature/competitive-generation`

**Status:** ✅ DONE

**What was done:**

- ✅ Implemented `generate_competitive_tests()` in `impl/scripts/generate_competitive.py`
- ✅ Created competitive prompt strategies in `impl/prompts/competitive/`:
  - `adversarial.txt` - Adversarial testing with gap analysis and fault-based testing principles
  - `diversity.txt` - Test diversity optimization based on test suite diversity metrics
  - `coverage.txt` - Coverage-guided test generation targeting uncovered code paths
- ✅ Implemented competitive workflow:
  - Agent 1 generates initial tests using standard test generation
  - Agent 2 reviews Agent 1's tests and generates competing tests based on competition mode
  - Tests are merged and deduplicated
- ✅ Implemented deduplication:
  - Compare test similarity using normalized string comparison
  - Remove duplicates by function name and code content
  - Preserve diverse test set

**Implementation details:**

- **Competitive Templates**: Located in `impl/prompts/competitive/` with placeholders for `{code_under_test}`, `{existing_tests}`, and `{num_tests}`
- **Competitive Workflow**: Two-agent competitive process where Agent 2 reviews and competes against Agent 1's tests
- **Competition Modes**: Three modes based on testing research (adversarial, diversity, coverage)
- **Test Extraction**: Uses AST parsing to extract top-level test functions
- **Deduplication**: Removes duplicates by name and normalized code comparison
- **Error Handling**: Robust error handling with graceful degradation
- **Validation**: Validates both individual agent responses and final merged code

**Manual steps completed:**

- ✅ Created feature branch: `feature/competitive-generation`
- ✅ Created competitive prompt strategy files in `impl/prompts/competitive/`
- ✅ Implemented complete competitive workflow logic
- ✅ Implemented test merging and deduplication
- ✅ Added comprehensive error handling and logging
- ✅ Enhanced with academic rigor and research alignment
- ✅ Committed and merged to main branch

---

## Step 6: Implement Evaluation Scripts

**Branch:** `feature/evaluation-scripts`

**Status:** ✅ COMPLETED

**What was done:**

- Implemented `run_pytest()` in `impl/scripts/run_pytest.py`
- Implemented `eval_coverage()` in `impl/scripts/eval_coverage.py`
- Implemented `eval_mutation()` in `impl/scripts/eval_mutation.py`
- Implemented `eval_diversity()` in `impl/scripts/eval_diversity.py`

**Manual steps:**

1. Create branch: `git checkout -b feature/evaluation-scripts`
2. **Implement run_pytest.py:**
   - Add CUT module to PYTHONPATH
   - Run `subprocess.run(["pytest", test_dir, ...])`
   - Capture output and exit code
   - Save results if output_file specified
3. **Implement eval_coverage.py:**
   - Use `coverage run` to execute tests
   - Use `coverage report` to get metrics
   - Parse coverage percentages
   - Generate report in specified format
   - Save to results directory
4. **Implement eval_mutation.py:**
   - Configure mutmut for CUT module
   - Run `mutmut run`
   - Parse mutmut results
   - Calculate mutation score: `killed / (killed + survived)`
   - Save results to results directory
5. **Implement eval_diversity.py:**
   - Parse all test files using AST
   - Calculate syntactic diversity (AST similarity)
   - Calculate semantic diversity (input value analysis)
   - Calculate coverage diversity (overlap analysis)
   - Save metrics to results directory
6. Test each evaluation script independently
7. Commit: `git commit -m "feat: implement evaluation scripts"`
8. Merge to main: `git checkout main && git merge feature/evaluation-scripts`

---

## Step 7: Implement Result Aggregation

**Branch:** `feature/result-aggregation`

**Status:** ✅ DONE

**What was done:**

- Implemented `aggregate_results()` in `impl/scripts/aggregate.py`
- Parsed results from all evaluation scripts
- Generated comparison tables / summary rows using pandas
- Exported in multiple formats (CSV, JSON, HTML)

**Manual steps:**

1. Create branch: `git checkout -b feature/result-aggregation`
2. Implement result parsing:
   - Scan `results/` directory
   - Parse coverage results
   - Parse mutation results
   - Parse diversity results
3. Implement aggregation:
   - Group by generation method (single, collab, competitive)
   - Calculate statistics (mean, std, min, max)
   - Create comparison tables
4. Implement export:
   - CSV format using pandas
   - JSON format
   - HTML format with tables
5. Test with sample results
6. Commit: `git commit -m "feat: implement result aggregation"`
7. Merge to main: `git checkout main && git merge feature/result-aggregation`

---

## Step 8: Integration Testing & Documentation

**Branch:** `feature/integration-testing`

**Status:** ✅ DONE

**What was done:**

- ✅ Created sample CUT modules for testing:
  - `calculator.py` - Simple arithmetic functions (already existed)
  - `string_utils.py` - String manipulation functions (reverse, capitalize, count_words, is_palindrome, etc.)
  - `data_structures.py` - Basic data structure operations (Stack, Queue, list utilities)
- ✅ Verified module imports and structure
- ✅ Fixed integration issues (incorrect imports in generated test files)
- ✅ Updated `impl/README.md` with comprehensive documentation:
  - Known issues section (LLM requirements, generated test quality, evaluation limitations)
  - Performance notes (execution times, resource requirements, LLM API considerations)
  - Example outputs (test generation, coverage, mutation, diversity, aggregated results)
  - Complete end-to-end workflow example
  - Troubleshooting guide
  - Best practices

**Implementation details:**

- **CUT Modules**: All three modules (`calculator`, `string_utils`, `data_structures`) are functional and ready for testing
- **Integration Issues Fixed**: Corrected import statements in existing generated test files
- **Documentation**: Comprehensive README with troubleshooting, performance notes, and examples

**Manual steps completed:**

- ✅ Created `string_utils.py` with 10 string manipulation functions
- ✅ Created `data_structures.py` with Stack, Queue classes and list utility functions
- ✅ Verified all modules import successfully
- ✅ Fixed import issues in existing test files
- ✅ Updated README with comprehensive documentation
- ✅ Documented known issues and limitations
- ✅ Added performance notes and example outputs

**Testing Instructions:**

See the "Manual Testing Guide" section below for detailed instructions on how to test the complete pipeline and interpret results.

---

## Step 9: HumanEval CUT Curation

**Branch:** `feature/integration-testing` (continue) or a new branch like `feature/humaneval-cut`

**Status:** ✅ DONE

**Why this step exists (A1):**

The A1 minimum requirements specify **10–20 functions/methods** chosen from an allowed source such as **public datasets (MBPP, HumanEval, CodeNet subsets)**. The current CUT modules in `impl/cut/` (`calculator.py`, `string_utils.py`, `data_structures.py`) are **synthetic samples** and do not satisfy the “dataset/source provenance” requirement by themselves.

**What was done:**

- ✅ Downloaded HumanEval dataset (`human-eval-v2-20210705.jsonl`)
- ✅ Selected **19 diverse standalone functions** covering multiple categories:
  - Math/statistics: `truncate_number`, `mean_absolute_deviation`, `greatest_common_divisor`, `sum_product`, `rescale_to_unit`, `factorize`
  - List operations: `has_close_elements`, `below_zero`, `intersperse`, `rolling_max`, `sort_numbers`, `find_closest_elements`, `remove_duplicates`
  - String operations: `parse_nested_parens`, `filter_by_substring`, `make_palindrome`, `string_xor`, `count_distinct_characters`, `flip_case`
- ✅ Created importable module: `impl/cut/humaneval_subset.py`
- ✅ Added provenance comments per function (task_id, entry_point, dataset source)

**Dataset Information:**

- **Source**: OpenAI HumanEval dataset
- **Download**: https://github.com/openai/human-eval
- **License**: MIT License
- **Dataset file**: `impl/human-eval-v2-20210705.jsonl` (164 programming problems)
- **Selected functions**: 19 functions from HumanEval tasks 0, 2-11, 13, 16, 19-21, 25-27

**Implementation details:**

- Functions extracted from HumanEval JSONL format (prompt + canonical_solution)
- All functions are standalone and importable
- Provenance comments include: task_id (e.g., "HumanEval/0"), entry_point (function name), and dataset file reference
- Functions maintain original docstrings and type hints
- No external dependencies beyond Python standard library

**Manual steps completed:**

- ✅ Downloaded HumanEval dataset to `impl/human-eval-v2-20210705.jsonl`
- ✅ Created Python script to parse JSONL and extract functions
- ✅ Selected 19 diverse functions based on algorithmic diversity
- ✅ Generated `impl/cut/humaneval_subset.py` with proper provenance
- ✅ Validated file syntax and importability

---

## Step 10: End-to-end Experiments + Results Capture

**Branch:** `feature/integration-testing` (continue) or a new branch like `feature/experiments-humaneval`

**Status:** ⏳ PENDING

**Goal (A1):**

Produce experimental evidence that compares:

- Single-agent baseline
- Collaborative multi-agent (≥2 roles)
- Competitive multi-agent

using at least one evaluation method (this repo supports **coverage**, **mutation**, and **diversity**).

**What needs to be done:**

- Run generation for `humaneval_subset` in all three modes (single/collab/competitive)
- Run pytest for each mode
- Run evaluations (coverage, mutation, diversity)
- Aggregate results into CSV/HTML in `impl/results/`

**Manual steps (example commands):**

```bash
cd impl

# Generate tests (all modes)
python scripts/generate_single.py --cut-module humaneval_subset --num-tests 10
python scripts/generate_collab.py --cut-module humaneval_subset --num-agents 3 --num-tests 10
python scripts/generate_competitive.py --cut-module humaneval_subset --num-agents 2 --num-tests 10 --competition-mode adversarial

# Run tests
python scripts/run_pytest.py --test-dir tests_generated/single --cut-module-path cut
python scripts/run_pytest.py --test-dir tests_generated/collab --cut-module-path cut
python scripts/run_pytest.py --test-dir tests_generated/competitive --cut-module-path cut

# Evaluate (write outputs into impl/results/)
python scripts/eval_coverage.py --test-dir tests_generated/single --cut-module humaneval_subset --output-file results/coverage_humaneval_subset_single.json --report-format json
python scripts/eval_mutation.py --test-dir tests_generated/single --cut-module humaneval_subset --output-file results/mutation_humaneval_subset_single.json
python scripts/eval_diversity.py --test-dir tests_generated/single --output-file results/diversity_humaneval_subset_single.json --diversity-metric syntactic

# Aggregate
python scripts/aggregate.py --results-dir results --output-file results/results_summary.csv --output-format csv
python scripts/aggregate.py --results-dir results --output-file results/results_summary.html --output-format html
```

**Notes:**

- You must have a local LLM server running (default: Ollama at `http://localhost:11434/api/generate`) and Python dependencies installed.
- Generated tests may require iteration (fix imports/assertions or regenerate) before evaluation metrics are meaningful.

---

## Manual Testing Guide

This section provides step-by-step instructions for manually testing the complete pipeline and understanding the results.

### Prerequisites

1. **Install Dependencies:**

   ```bash
   cd impl
   pip install -e .
   # Or manually: pip install pytest coverage mutmut pandas requests
   ```

2. **Start LLM Service (Ollama):**

   ```bash
   # Install Ollama if not already installed: https://ollama.ai
   ollama serve
   # In another terminal, pull a model:
   ollama pull llama3.2:1b  # or llama3.2:3b for better quality
   ```

3. **Set Environment Variables (Optional):**
   ```bash
   export OLLAMA_MODEL=llama3.2:1b
   export OLLAMA_API_URL=http://localhost:11434/api/generate
   ```

### Step-by-Step Testing Workflow

#### 1. Generate Tests for a CUT Module

**Single-Agent Generation:**

```bash
cd impl
python scripts/generate_single.py --cut-module calculator --num-tests 10
```

**What to expect:**

- Script loads the CUT module
- Calls LLM to generate test code
- Validates and saves tests to `tests_generated/single/test_calculator.py`
- Output shows: number of test functions generated, file size, validation status

**Collaborative Generation:**

```bash
python scripts/generate_collab.py --cut-module calculator --num-agents 3 --num-tests 10
```

**What to expect:**

- Three agents generate tests sequentially (edge cases, boundary, integration)
- Tests are merged and deduplicated
- Output shows: tests per agent, deduplication results, final test count

**Competitive Generation:**

```bash
python scripts/generate_competitive.py --cut-module calculator --num-agents 2 --num-tests 10 --competition-mode adversarial
```

**What to expect:**

- Agent 1 generates initial tests
- Agent 2 reviews and generates competing tests
- Output shows: tests from each agent, deduplication results

**Repeat for other modules:**

```bash
python scripts/generate_single.py --cut-module string_utils --num-tests 10
python scripts/generate_single.py --cut-module data_structures --num-tests 10
```

#### 2. Run Generated Tests

```bash
# Test single-agent generated tests
python scripts/run_pytest.py --test-dir tests_generated/single --cut-module-path cut

# Test collaborative generated tests
python scripts/run_pytest.py --test-dir tests_generated/collab --cut-module-path cut

# Test competitive generated tests
python scripts/run_pytest.py --test-dir tests_generated/competitive --cut-module-path cut
```

**What to expect:**

- Pytest runs all test functions
- Shows pass/fail status for each test
- Some tests may fail (this is normal - LLM-generated tests aren't always perfect)
- Exit code 0 = all passed, non-zero = some failed

**Understanding Results:**

- ✅ **All tests pass**: Generated tests are correct
- ⚠️ **Some tests fail**: Review failures - may need to fix imports or assertions
- ❌ **Many tests fail**: Consider regenerating with different parameters or model

#### 3. Evaluate Test Coverage

```bash
python scripts/eval_coverage.py --test-dir tests_generated/single --cut-module calculator
```

**What to expect:**

- Runs tests with coverage tracking
- Generates JSON file: `results/coverage_calculator_single.json`
- Output shows line and branch coverage percentages

**Understanding Coverage Results:**

```json
{
  "line": 0.85, // 85% of lines executed
  "branch": 0.72, // 72% of branches executed
  "module": "calculator"
}
```

- **Line Coverage**: Percentage of code lines executed by tests
- **Branch Coverage**: Percentage of conditional branches tested
- **Good coverage**: >80% line, >70% branch
- **Poor coverage**: <50% - tests may be missing important code paths

#### 4. Evaluate Mutation Testing

```bash
python scripts/eval_mutation.py --test-dir tests_generated/single --cut-module calculator
```

**What to expect:**

- Runs mutmut to create mutations of the CUT
- Tests each mutation against the test suite
- Takes 2-10 minutes depending on module size
- Generates JSON file: `results/mutation_calculator_single.json`

**Understanding Mutation Results:**

```json
{
  "score": 0.75, // 75% mutation score
  "killed": 15, // 15 mutations killed (caught by tests)
  "survived": 5, // 5 mutations survived (tests didn't catch)
  "timeout": 0, // Mutations that timed out
  "suspicious": 0, // Suspicious mutations
  "skipped": 0 // Skipped mutations
}
```

- **Mutation Score**: `killed / (killed + survived)` - higher is better
- **Killed**: Mutations detected by tests (good - tests are effective)
- **Survived**: Mutations not detected (bad - tests may be weak)
- **Good score**: >70% - tests are effective at catching bugs
- **Poor score**: <50% - tests may not be thorough enough

#### 5. Evaluate Test Diversity

```bash
python scripts/eval_diversity.py --test-dir tests_generated/single
```

**What to expect:**

- Analyzes test files using AST parsing
- Calculates syntactic, semantic, and coverage diversity metrics
- Generates JSON file: `results/diversity_calculator_single.json`

**Understanding Diversity Results:**

```json
{
  "diversity_score": 0.65, // Overall diversity (0-1)
  "unique_ast_patterns": 13, // Unique code structures
  "unique_assertions": 8, // Unique assertion patterns
  "unique_calls": 6, // Unique function calls
  "unique_values": 25, // Unique input values
  "total_values": 40, // Total input values
  "edge_case_count": 5, // Number of edge case tests
  "total_tests": 10 // Total test functions
}
```

- **Diversity Score**: How different tests are from each other (higher = more diverse)
- **Unique Patterns**: More unique patterns = better test variety
- **Edge Cases**: Higher count = better edge case coverage
- **Good diversity**: >0.6 - tests cover different scenarios
- **Poor diversity**: <0.4 - tests may be too similar/redundant

#### 6. Aggregate Results

```bash
python scripts/aggregate.py --results-dir results --output-file results_summary.csv
```

**What to expect:**

- Scans `results/` directory for all JSON result files
- Combines coverage, mutation, and diversity metrics
- Generates CSV file: `results/results_summary.csv`

**Understanding Aggregated Results:**

The CSV file contains one row per (CUT, mode, metric_type) combination:

| file                             | cut        | mode   | metric_type | coverage_line | coverage_branch | mutation_score | mutation_killed | mutation_survived | diversity_score |
| -------------------------------- | ---------- | ------ | ----------- | ------------- | --------------- | -------------- | --------------- | ----------------- | --------------- |
| coverage_calculator_single.json  | calculator | single | coverage    | 0.85          | 0.72            |                |                 |                   |                 |
| mutation_calculator_single.json  | calculator | single | mutation    |               |                 | 0.75           | 15              | 5                 |                 |
| diversity_calculator_single.json | calculator | single | diversity   |               |                 |                |                 |                   | 0.65            |

**Comparing Generation Methods:**

Compare rows with same `cut` but different `mode`:

- **single**: Single-agent generation
- **collab**: Collaborative generation (multiple specialized agents)
- **competitive**: Competitive generation (adversarial agents)

**What to look for:**

- Which method produces highest coverage?
- Which method has best mutation score?
- Which method generates most diverse tests?
- Trade-offs: collab/competitive may take longer but produce better results

### Complete Example: Testing Calculator Module

```bash
cd impl

# 1. Generate tests (all three methods)
python scripts/generate_single.py --cut-module calculator --num-tests 10
python scripts/generate_collab.py --cut-module calculator --num-agents 3 --num-tests 10
python scripts/generate_competitive.py --cut-module calculator --num-agents 2 --num-tests 10

# 2. Run tests
python scripts/run_pytest.py --test-dir tests_generated/single --cut-module-path cut
python scripts/run_pytest.py --test-dir tests_generated/collab --cut-module-path cut
python scripts/run_pytest.py --test-dir tests_generated/competitive --cut-module-path cut

# 3. Evaluate quality
python scripts/eval_coverage.py --test-dir tests_generated/single --cut-module calculator
python scripts/eval_coverage.py --test-dir tests_generated/collab --cut-module calculator
python scripts/eval_coverage.py --test-dir tests_generated/competitive --cut-module calculator

python scripts/eval_mutation.py --test-dir tests_generated/single --cut-module calculator
python scripts/eval_mutation.py --test-dir tests_generated/collab --cut-module calculator
python scripts/eval_mutation.py --test-dir tests_generated/competitive --cut-module calculator

python scripts/eval_diversity.py --test-dir tests_generated/single
python scripts/eval_diversity.py --test-dir tests_generated/collab
python scripts/eval_diversity.py --test-dir tests_generated/competitive

# 4. Aggregate and compare
python scripts/aggregate.py --results-dir results --output-file results_summary.csv

# 5. View results
cat results/results_summary.csv
```

### Interpreting Results Summary

After running the complete pipeline, you'll have:

1. **Generated Test Files**: `tests_generated/{single,collab,competitive}/test_*.py`
   - Review these to understand what tests were generated
   - Check for import errors or incorrect assertions

2. **Coverage Reports**: `results/coverage_*_*.json`
   - Compare line/branch coverage across methods
   - Identify which method achieves best coverage

3. **Mutation Reports**: `results/mutation_*_*.json`
   - Compare mutation scores
   - Higher scores = better test quality

4. **Diversity Reports**: `results/diversity_*_*.json`
   - Compare diversity scores
   - Higher diversity = more varied test scenarios

5. **Aggregated Summary**: `results/results_summary.csv`
   - Side-by-side comparison of all metrics
   - Use to determine which generation method works best for your use case

### Common Issues and Solutions

**Issue**: LLM connection errors

- **Solution**: Ensure Ollama is running (`ollama serve`)
- **Check**: `curl http://localhost:11434/api/tags`

**Issue**: Import errors in generated tests

- **Solution**: Manually fix imports (change `from simple_calculator import` to `from impl.cut.calculator import`)
- **Prevention**: Review generated tests before committing

**Issue**: Many test failures

- **Solution**: Regenerate with different parameters or larger model
- **Alternative**: Manually fix obvious errors in generated tests

**Issue**: Low coverage/mutation scores

- **Solution**: Generate more tests or use collaborative/competitive methods
- **Check**: Review CUT module - may need better docstrings for LLM to understand

**Issue**: Evaluation scripts fail

- **Solution**: Ensure dependencies installed (`pip install coverage mutmut pandas`)
- **Check**: Verify Python version (3.8+)

### Tips for Best Results

1. **Start with simple modules** (like `calculator`) before testing complex code
2. **Use collaborative or competitive** generation for better quality (though slower)
3. **Review generated tests** - don't blindly trust LLM output
4. **Iterate**: If results are poor, try different parameters or models
5. **Compare methods**: Use aggregated results to see which works best
6. **Fix obvious errors**: Manually correct import statements and clear bugs

## Notes

- Always test each feature independently before merging
- Keep commits atomic and well-documented
- Update this guide as you progress through steps
- Add any additional manual steps you discover during implementation
- Refer to `impl/README.md` for detailed usage instructions and troubleshooting
