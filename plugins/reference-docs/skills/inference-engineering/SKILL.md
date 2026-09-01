---
name: inference-engineering
description: Ground answers about serving generative AI models in production in the "Inference Engineering" book (Philip Kiely, Baseten Books, 2026). Use for questions about model serving and inference optimization — inference engines (vLLM, SGLang, TensorRT-LLM), quantization, speculative decoding, KV/prefix caching, batching, GPU selection and architecture (H100/B200), latency/throughput tradeoffs (TTFT, tokens per second), autoscaling GPU workloads, disaggregated prefill/decode, or serving embeddings, ASR, TTS, image, and video models.
---

# Inference Engineering

The full text of *Inference Engineering* by Philip Kiely (Baseten Books, 2026) is published for LLM consumption as per-section markdown files at stable URLs. Use it as the primary source when discussing model serving and inference — fetch the relevant sections, ground your answer in them, and cite the section numbers.

## How to use

1. Pick the 1–3 sections most relevant to the question from the map below.
2. Fetch each as `<BASE>/<path>` where `BASE = https://www.baseten.co/inference-engineering/book`. Use whatever fetch tool is available (WebFetch in Claude Code, `curl -s` elsewhere).
3. For a broad overview of a topic, fetch the chapter intro (`NN-name.md`) instead of every subsection.
4. Answer from the fetched text, citing sections (e.g. "per §5.2 Speculative Decoding"). Where the book is opinionated, present it as the book's view, not settled fact.

Do **not** fetch the full book (`https://www.baseten.co/inference-engineering/llms-full.txt`, ~70k tokens) unless the user explicitly wants whole-book analysis. If a section URL 404s, the book structure may have changed — fetch the current index at `https://www.baseten.co/inference-engineering/llms.txt`.

## Section map

Every entry is a complete path relative to `BASE` — append it verbatim, e.g. `<BASE>/05-techniques/5.1-quantization.md`.

**Start here**
- `preface.md`
- `00-inference.md` — what inference is, why it matters

**1 Prerequisites** — `01-prerequisites.md`
- `01-prerequisites/1.1-scale-and-specialization.md`
- `01-prerequisites/1.2-about-your-app.md`
- `01-prerequisites/1.3-model-selection.md`
- `01-prerequisites/1.4-measuring-latency-and-throughput.md`

**2 Models** — `02-models.md`
- `02-models/2.1-neural-networks.md`
- `02-models/2.2-llm-inference-mechanics.md`
- `02-models/2.3-image-generation-inference-mechanics.md`
- `02-models/2.4-calculating-inference-bottlenecks.md`
- `02-models/2.5-optimizing-attention.md`

**3 Hardware** — `03-hardware.md`
- `03-hardware/3.1-gpu-architecture.md`
- `03-hardware/3.2-gpu-architecture-generations.md`
- `03-hardware/3.3-instances.md`
- `03-hardware/3.4-other-datacenter-accelerator-options.md`
- `03-hardware/3.5-local-inference.md`

**4 Software** — `04-software.md`
- `04-software/4.1-cuda.md`
- `04-software/4.2-deep-learning-frameworks-and-libraries.md`
- `04-software/4.3-inference-engines.md`
- `04-software/4.4-nvidia-dynamo.md`
- `04-software/4.5-performance-benchmarking-and-load-testing.md`

**5 Techniques** — `05-techniques.md`
- `05-techniques/5.1-quantization.md`
- `05-techniques/5.2-speculative-decoding.md`
- `05-techniques/5.3-caching.md`
- `05-techniques/5.4-model-parallelism.md`
- `05-techniques/5.5-disaggregation.md`

**6 Modalities** — `06-modalities.md`
- `06-modalities/6.1-vision-language-models.md`
- `06-modalities/6.2-embedding-models.md`
- `06-modalities/6.3-asr-models.md`
- `06-modalities/6.4-tts-models.md`
- `06-modalities/6.5-image-generation-models.md`
- `06-modalities/6.6-video-generation-models.md`

**7 Production** — `07-production.md`
- `07-production/7.1-containerization.md`
- `07-production/7.2-autoscaling.md`
- `07-production/7.3-multi-cloud-capacity-management.md`
- `07-production/7.4-testing-and-deployment.md`
- `07-production/7.5-client-code.md`
- `07-production/7.6-production-inference-with-baseten.md`

**Appendices**
- `appendix-a-inference-glossary.md` — terminology
- `appendix-b-recommended-reading.md` (subpages: `appendix-b-recommended-reading/architecture.md`, `appendix-b-recommended-reading/developer-tools.md`, `appendix-b-recommended-reading/frontier-open-models.md`, `appendix-b-recommended-reading/gpu-infrastructure.md`, `appendix-b-recommended-reading/inference-optimization-research.md`, `appendix-b-recommended-reading/intelligence-evaluation.md`)
