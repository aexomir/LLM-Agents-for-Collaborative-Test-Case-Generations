# Experiment Report

**Experiment ID:** humaneval_subset_20260129_031531
**Created:** 2026-01-29T03:15:31.510536
**Last Updated:** 2026-01-29T03:26:09.626827

## Configuration

```yaml
aggregation:
  enabled: true
  formats:
  - csv
  - html
cut_module: humaneval_subset
evaluation:
  coverage:
    enabled: true
    report_format: json
  diversity:
    enabled: true
    metric: syntactic
  pytest:
    enabled: true
    verbose: false
experiment:
  description: Compare single/collab/competitive test generation
  id: humaneval_subset_20260129_031531
  name: Step 10 Experiment
generation:
  collab:
    enabled: true
    num_agents: 3
    num_tests: 10
  competitive:
    competition_mode: adversarial
    enabled: true
    num_agents: 2
    num_tests: 10
  single:
    enabled: true
    num_tests: 10
logging:
  console: true
  file: true
  format: detailed
  level: INFO
num_tests: 10
output:
  base_dir: results/experiments
  create_timestamped_dirs: true

```

## Test Generation Results

### Single Mode

- **Test Directory:** `/Users/aexomir/Desktop/LLM/impl/tests_generated/single/20260129_031531`
- **Run ID:** 20260129_031531
- **Timestamp:** 2026-01-29T03:26:07.584713

### Collab Mode

- **Test Directory:** `/Users/aexomir/Desktop/LLM/impl/tests_generated/collab/20260129_032015`
- **Run ID:** 20260129_032015
- **Timestamp:** 2026-01-29T03:26:07.585240

### Competitive Mode

- **Test Directory:** `/Users/aexomir/Desktop/LLM/impl/tests_generated/competitive/20260129_032333`
- **Run ID:** 20260129_032333
- **Timestamp:** 2026-01-29T03:26:07.585554

## Evaluation Results

### Coverage Metrics

| Mode | Result File |
|------|-------------|
| single | `/Users/aexomir/Desktop/LLM/results/experiments/humaneval_subset_20260129_031531/metrics/coverage_humaneval_subset_single.json` |
| collab | `/Users/aexomir/Desktop/LLM/results/experiments/humaneval_subset_20260129_031531/metrics/coverage_humaneval_subset_collab.json` |
| competitive | `/Users/aexomir/Desktop/LLM/results/experiments/humaneval_subset_20260129_031531/metrics/coverage_humaneval_subset_competitive.json` |

### Diversity Metrics

| Mode | Result File |
|------|-------------|
| single | `/Users/aexomir/Desktop/LLM/results/experiments/humaneval_subset_20260129_031531/metrics/diversity_humaneval_subset_single.json` |
| collab | `/Users/aexomir/Desktop/LLM/results/experiments/humaneval_subset_20260129_031531/metrics/diversity_humaneval_subset_collab.json` |
| competitive | `/Users/aexomir/Desktop/LLM/results/experiments/humaneval_subset_20260129_031531/metrics/diversity_humaneval_subset_competitive.json` |

## Validation Status

✓ All results validated successfully
