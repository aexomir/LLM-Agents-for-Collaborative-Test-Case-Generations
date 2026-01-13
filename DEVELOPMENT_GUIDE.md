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
