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

**Status:** ⏳ PENDING

**What needs to be done:**

- Implement `generate_single_tests()` in `impl/scripts/generate_single.py`
- Load CUT module dynamically
- Create prompt templates in `impl/prompts/patterns/`
- Call LLM to generate test code
- Parse and validate generated Python code
- Save as valid pytest files

**Manual steps:**

1. Create branch: `git checkout -b feature/single-agent-generation`
2. Create prompt template in `impl/prompts/patterns/single_agent.txt`:

   ```
   Generate pytest test cases for the following Python function:

   {code_under_test}

   Requirements:
   - Use pytest conventions (test_ prefix)
   - Include edge cases
   - Test both positive and negative cases
   - Add docstrings to test functions
   ```

3. Implement dynamic module loading:
   ```python
   import importlib
   cut_module = importlib.import_module(f"impl.cut.{cut_module_name}")
   ```
4. Implement code generation:
   - Load prompt template
   - Format prompt with CUT code
   - Call `call_local_llm()`
   - Extract Python code from LLM response
5. Implement code validation:
   - Parse generated code with `ast.parse()`
   - Ensure test functions start with `test_`
   - Validate pytest syntax
6. Save generated tests to `output_dir` as `.py` files
7. Test with a sample CUT module
8. Commit: `git commit -m "feat: implement single-agent test generation"`
9. Merge to main: `git checkout main && git merge feature/single-agent-generation`

---

## Step 4: Implement Collaborative Test Generation

**Branch:** `feature/collaborative-generation`

**Status:** ⏳ PENDING

**What needs to be done:**

- Implement `generate_collab_tests()` in `impl/scripts/generate_collab.py`
- Create role definitions in `impl/prompts/roles/`
- Coordinate multiple LLM calls with different roles
- Merge/combine test cases from different agents

**Manual steps:**

1. Create branch: `git checkout -b feature/collaborative-generation`
2. Create role definitions in `impl/prompts/roles/`:
   - `tester_edge_cases.txt` - Focus on edge cases
   - `tester_boundary.txt` - Focus on boundary conditions
   - `tester_integration.txt` - Focus on integration scenarios
3. Implement multi-agent coordination:
   - Load role definitions
   - Create prompts for each agent with their role
   - Call `call_local_llm()` for each agent
   - Collect responses
4. Implement test merging:
   - Deduplicate similar tests
   - Combine complementary test cases
   - Ensure no conflicts
5. Save merged tests to `output_dir`
6. Test with a sample CUT module
7. Commit: `git commit -m "feat: implement collaborative test generation"`
8. Merge to main: `git checkout main && git merge feature/collaborative-generation`

---

## Step 5: Implement Competitive Test Generation

**Branch:** `feature/competitive-generation`

**Status:** ⏳ PENDING

**What needs to be done:**

- Implement `generate_competitive_tests()` in `impl/scripts/generate_competitive.py`
- Set up competitive prompt strategies
- Run multiple LLM calls with competitive objectives
- Collect and deduplicate test cases

**Manual steps:**

1. Create branch: `git checkout -b feature/competitive-generation`
2. Create competitive prompt strategies:
   - Adversarial: "Find bugs and edge cases the other agent missed"
   - Diversity: "Generate tests that are different from existing ones"
   - Coverage: "Generate tests that cover uncovered code paths"
3. Implement competitive loop:
   - Agent 1 generates initial tests
   - Agent 2 reviews and generates competing tests
   - Iterate until convergence or max iterations
4. Implement deduplication:
   - Compare test similarity (AST or semantic)
   - Remove duplicates
   - Keep diverse test set
5. Save competitive tests to `output_dir`
6. Test with a sample CUT module
7. Commit: `git commit -m "feat: implement competitive test generation"`
8. Merge to main: `git checkout main && git merge feature/competitive-generation`

---

## Step 6: Implement Evaluation Scripts

**Branch:** `feature/evaluation-scripts`

**Status:** ⏳ PENDING

**What needs to be done:**

- Implement `run_pytest()` in `impl/scripts/run_pytest.py`
- Implement `eval_coverage()` in `impl/scripts/eval_coverage.py`
- Implement `eval_mutation()` in `impl/scripts/eval_mutation.py`
- Implement `eval_diversity()` in `impl/scripts/eval_diversity.py`

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

**Status:** ⏳ PENDING

**What needs to be done:**

- Implement `aggregate_results()` in `impl/scripts/aggregate.py`
- Parse results from all evaluation scripts
- Generate comparison tables
- Export in multiple formats (CSV, JSON, HTML)

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

**Status:** ⏳ PENDING

**What needs to be done:**

- Create sample CUT modules for testing
- Run end-to-end pipeline
- Fix any integration issues
- Update documentation

**Manual steps:**

1. Create branch: `git checkout -b feature/integration-testing`
2. Create sample CUT modules in `impl/cut/`:
   - `calculator.py` - Simple arithmetic functions
   - `string_utils.py` - String manipulation functions
   - `data_structures.py` - Basic data structure operations
3. Run full pipeline for each CUT:

   ```bash
   # Generate tests
   python scripts/generate_single.py --cut-module calculator --num-tests 10
   python scripts/generate_collab.py --cut-module calculator --num-agents 3
   python scripts/generate_competitive.py --cut-module calculator --num-agents 2

   # Evaluate tests
   python scripts/run_pytest.py --test-dir tests_generated/single --cut-module-path cut
   python scripts/eval_coverage.py --test-dir tests_generated/single --cut-module calculator
   python scripts/eval_mutation.py --test-dir tests_generated/single --cut-module calculator
   python scripts/eval_diversity.py --test-dir tests_generated/single

   # Aggregate results
   python scripts/aggregate.py --results-dir results --output-file results_summary.csv
   ```

4. Fix any bugs or integration issues
5. Update `impl/README.md` with:
   - Known issues
   - Performance notes
   - Example outputs
6. Commit: `git commit -m "feat: add integration testing and documentation"`
7. Merge to main: `git checkout main && git merge feature/integration-testing`

---

## Notes

- Always test each feature independently before merging
- Keep commits atomic and well-documented
- Update this guide as you progress through steps
- Add any additional manual steps you discover during implementation
