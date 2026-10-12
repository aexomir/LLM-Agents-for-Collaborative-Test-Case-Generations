# Multi-Agent LLM Test Generation: Single, Collaborative and Competitive Agents

We compare three ways of using large language models (LLMs) to write Python unit tests: one agent, several collaborating agents, and several competing agents.

## Overview

Writing unit tests by hand is slow, and classic test generators often need expert setup. We study how the way LLM agents are organized changes the tests they produce.

- **Single agent.** One agent writes the whole test suite from one prompt. A quality check looks for assertions, imports and function calls, and retries if the result is too weak.
- **Collaborative agents.** Three agents with fixed roles write tests: one for edge cases, one for boundary values, one for integration-style usage. Their tests are merged into one file and duplicates are removed.
- **Competitive agents.** Two agents work in an adversarial setup. The second agent looks at the first agent's tests and tries to cover the gaps they leave.

## Method

- **Dataset.** A curated subset of 19 functions from HumanEval (math, list and string functions). The functions are in `impl/cut/humaneval_subset.py`. The original dataset file is `impl/human-eval-v2-20210705.jsonl`.
- **Metrics.** Line coverage and branch coverage, measured with pytest and coverage.py. Test diversity, measured on the test code's syntax tree: a diversity score, unique syntactic patterns, and unique assertions.
- **LLM backend.** By default the code calls a local Ollama server with the model `qwen2.5-coder:14b-instruct`. This is the setup used in the paper. The code can also call the OpenAI API instead (see Setup and run).

## Results

Numbers from the paper, one experiment run on the 19 functions.

| Approach      | Line coverage | Branch coverage | Diversity score | Unique test patterns |
|---------------|---------------|-----------------|-----------------|----------------------|
| Single agent  | 22.9%         | –               | 0.598           | –                    |
| Collaborative | 9.7%          | 0%              | –               | –                    |
| Competitive   | –             | 11.1%           | –               | 20                   |

The low collaborative result likely comes from an aggressive deduplication step that removes tests which would exercise other branches; this is the paper's own explanation. The dataset is small (19 functions), so these results may not hold for other code.

The full tables are in the paper. The raw output of the run is in `results/experiments/`.

## Repository layout

```
impl/                  Python code
  cut/                 Code under test, including the 19-function HumanEval subset
  prompts/             Prompt templates for the single, collaborative and competitive agents
  scripts/             Test generators, evaluators, aggregation and the experiment runner
  scripts/configs/     Experiment configuration (YAML)
  src/                 LLM client (Ollama or OpenAI)
  tests/               Tests for the experiment runner
report/                Paper (PDF and LaTeX source)
results/experiments/   Metrics, reports and generated tests from the run used in the paper
```

`impl/DEVELOPMENT_GUIDE.md` describes each implementation step and the scripts in more detail.

## Setup and run

Requirements: Python 3.8 or newer, and [Ollama](https://ollama.com) for the default local model.

Install the dependencies (pytest, coverage, pandas, requests, pyyaml, colorama, tqdm):

```bash
cd impl
pip install -e .
cd ..
```

Start Ollama and download the model:

```bash
ollama serve
ollama pull qwen2.5-coder:14b-instruct
```

Optional environment variables:

- `OLLAMA_MODEL` (default `qwen2.5-coder:14b-instruct`) and `OLLAMA_API_URL` (default `http://localhost:11434/api/generate`).
- To use OpenAI instead, run `pip install openai` and set `OPENAI_API_KEY`. `OPENAI_MODEL` defaults to `gpt-4o-mini`. `LLM_PROVIDER=local` or `LLM_PROVIDER=openai` forces a provider.

Run the full experiment (all three approaches, evaluation and aggregation) from the repository root:

```bash
python impl/scripts/run_experiments.py
```

It reads `impl/scripts/configs/default_experiment.yaml` and writes to `results/experiments/<cut_module>_<timestamp>/` (`metrics/`, `reports/`, `tests/`, `logs/`).

Run one approach at a time, from the repository root:

```bash
python impl/scripts/generate_single.py --cut-module humaneval_subset --num-tests 10
python impl/scripts/generate_collab.py --cut-module humaneval_subset --num-agents 3 --num-tests 10
python impl/scripts/generate_competitive.py --cut-module humaneval_subset --num-agents 2 --num-tests 10 --competition-mode adversarial
```

Generated tests go to `impl/tests_generated/<single|collab|competitive>/<timestamp>/`. These folders are not tracked in git.

## Paper

[Multi-Agent LLM-Based Test Generation: A Comparative Study of Single, Collaborative, and Competitive Approaches](report/Multi-Agent%20LLM-Based%20Test%20Generation.pdf)

Kiana Salimi, AmirHossein Ranjbar, Sanam Alinezhad, Nazanin Hashemi. Politecnico di Torino, 2026.

## Acknowledgments

- HumanEval, by OpenAI (Chen et al., 2021, "Evaluating Large Language Models Trained on Code"), for the functions under test.
- The ACL style files, used to typeset the paper.
