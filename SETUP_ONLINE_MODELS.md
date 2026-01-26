# Using Online LLM Models (OpenAI) for Faster, Better Test Generation

This guide explains how to use online LLM APIs (like OpenAI) instead of local models for **faster** and **higher-quality** test generation.

## Why Use Online Models?

✅ **Much Faster**: Cloud GPUs are optimized and fast (seconds vs minutes)  
✅ **Better Quality**: Access to state-of-the-art models (GPT-4, GPT-4o, etc.)  
✅ **No Local Resources**: No need for local GPU/CPU, no memory constraints  
✅ **Reliable**: No timeout issues, consistent performance  
✅ **Cost-Effective**: Pay per use, often cheaper than maintaining local hardware  

## Quick Setup (OpenAI)

### Step 1: Install OpenAI Library

```bash
pip install openai
```

### Step 2: Get OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `sk-...`)

### Step 3: Set Environment Variable

**For current session:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

**For permanent (add to ~/.zshrc or ~/.bashrc):**
```bash
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Step 4: (Optional) Choose Model

Default is `gpt-4o-mini` (fast and cost-effective). To use a different model:

```bash
export OPENAI_MODEL="gpt-4o"        # Best quality, slower
export OPENAI_MODEL="gpt-4-turbo"    # Great balance
export OPENAI_MODEL="gpt-3.5-turbo" # Fastest, cheaper
```

### Step 5: Run Test Generation

The system will **automatically detect** `OPENAI_API_KEY` and use OpenAI:

```bash
python impl/scripts/generate_single.py --cut-module calculator --num-tests 10
```

You'll see output like:
```
Provider: openai
Model: gpt-4o-mini
```

## Model Recommendations

### For Speed + Quality Balance:
- **`gpt-4o-mini`** (default) - ⚡ Fast, 💰 Cheap, ✅ Good quality
- **`gpt-3.5-turbo`** - ⚡⚡ Very fast, 💰💰 Very cheap, ✅ Good quality

### For Best Quality:
- **`gpt-4o`** - ⚡ Fast, 💰 Moderate cost, ✅✅ Excellent quality
- **`gpt-4-turbo`** - ⚡ Moderate, 💰 Moderate cost, ✅✅ Excellent quality

### Cost Comparison (approximate per 1000 tests):
- `gpt-4o-mini`: ~$0.10-0.50
- `gpt-3.5-turbo`: ~$0.05-0.20
- `gpt-4o`: ~$0.50-2.00
- `gpt-4-turbo`: ~$1.00-3.00

## Performance Comparison

| Model Type | Speed | Quality | Setup |
|------------|-------|---------|-------|
| **OpenAI (gpt-4o-mini)** | ⚡⚡⚡ 5-15s | ✅✅✅ Excellent | Easy |
| **OpenAI (gpt-4o)** | ⚡⚡ 10-30s | ✅✅✅ Excellent | Easy |
| **Local (codellama:7b)** | ⚡ 30-300s | ✅✅ Good | Complex |
| **Local (llama3.2:1b)** | ⚡⚡ 10-60s | ✅ Basic | Easy |

## Usage Examples

### Single Agent with OpenAI
```bash
# Automatically uses OpenAI if OPENAI_API_KEY is set
python impl/scripts/generate_single.py --cut-module calculator --num-tests 10
```

### Collaborative with OpenAI
```bash
python impl/scripts/generate_collab.py \
    --cut-module calculator \
    --num-agents 3 \
    --num-tests 10
```

### Competitive with OpenAI
```bash
python impl/scripts/generate_competitive.py \
    --cut-module calculator \
    --num-agents 2 \
    --num-tests 10 \
    --competition-mode adversarial
```

## Switching Between Local and Online

### Use OpenAI (if API key is set):
```bash
export OPENAI_API_KEY="sk-your-key"
# System automatically uses OpenAI
```

### Force Local (Ollama):
```bash
unset OPENAI_API_KEY
export LLM_PROVIDER="local"
```

### Force OpenAI:
```bash
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="sk-your-key"
```

## Cost Management

### Monitor Usage:
- Check usage at: https://platform.openai.com/usage
- Set spending limits at: https://platform.openai.com/account/billing/limits

### Optimize Costs:
1. Use `gpt-4o-mini` for most tasks (10x cheaper than GPT-4)
2. Use `gpt-3.5-turbo` for simple test cases
3. Use `gpt-4o` only when you need highest quality
4. Reduce `max_tokens` in prompts (already optimized to 3000)

## Troubleshooting

### Issue: "OpenAI library not installed"
**Solution:**
```bash
pip install openai
```

### Issue: "OPENAI_API_KEY not set"
**Solution:**
```bash
export OPENAI_API_KEY="sk-your-api-key"
# Verify:
echo $OPENAI_API_KEY
```

### Issue: "Insufficient quota"
**Solution:**
- Check your OpenAI account billing
- Add payment method at: https://platform.openai.com/account/billing
- Or use a different model (gpt-3.5-turbo is cheaper)

### Issue: "Rate limit exceeded"
**Solution:**
- Wait a few minutes
- Reduce number of concurrent requests
- Upgrade your OpenAI plan

## Security Best Practices

1. **Never commit API keys** to git
2. **Use environment variables** (not hardcoded)
3. **Rotate keys** periodically
4. **Set spending limits** in OpenAI dashboard
5. **Monitor usage** regularly

## Comparison: Local vs Online

### When to Use Online (OpenAI):
- ✅ Need fast results (seconds not minutes)
- ✅ Want best quality
- ✅ Don't want to manage local hardware
- ✅ Have internet connection
- ✅ Budget allows API costs

### When to Use Local (Ollama):
- ✅ Need offline operation
- ✅ Have privacy/security concerns
- ✅ Want zero API costs
- ✅ Have powerful local GPU
- ✅ Working with sensitive code

## Quick Start Commands

```bash
# 1. Install OpenAI library
pip install openai

# 2. Set API key
export OPENAI_API_KEY="sk-your-key-here"

# 3. (Optional) Choose model
export OPENAI_MODEL="gpt-4o-mini"

# 4. Generate tests (automatically uses OpenAI)
python impl/scripts/generate_single.py --cut-module calculator --num-tests 10
```

## Expected Performance

With **OpenAI GPT-4o-mini**:
- ⚡ **Speed**: 5-15 seconds per generation
- ✅ **Quality**: Excellent (much better than local 1B/7B models)
- 💰 **Cost**: ~$0.10-0.50 per 1000 test generations
- 🎯 **Reliability**: 99.9% uptime, no timeouts

You should see **dramatic improvements** in both speed and quality compared to local models!
