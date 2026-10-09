#!/usr/bin/env python3
"""DarkSky Whisper: LoRA Fine-Tuning via Thinking Machines Tinker API.

Offloads distributed gradient computation and LoRA parameter optimization
to Thinking Machines' Tinker cloud infrastructure while controlling the training
loop, prompt masking, and dataset curriculum locally.

Trains Qwen/Qwen3.5-4B (or base open LLMs) on the 75 curated spoken astronomy pairs,
enforcing:
1. Zero markdown formatting (*, #, _, `, [, ])
2. 35-word natural spoken prose brevity
3. Immediate spatial direction (cardinal + altitude)
4. Atmospheric seeing integration
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

import numpy as np
from dotenv import load_dotenv

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

import tinker

DATASET_FILE = PROJECT_ROOT / "benchmarks" / "dataset" / "spoken_astronomy_pairs.jsonl"
REPORT_FILE = PROJECT_ROOT / "benchmarks" / "tinker_training_report.json"

SYSTEM_PROMPT = (
    "You are DarkSky Whisper, an eyes-free astronomical observatory companion resting face-down in the grass. "
    "The observer is looking at the night sky. In natural spoken English without any markdown, asterisks, bullet points, "
    "or greetings, answer their spoken query in under 40 words with cardinal directions and seeing stability."
)


def load_astronomy_pairs(dataset_path: Path) -> List[Dict[str, Any]]:
    """Load curated astronomical interaction pairs."""
    pairs = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def build_datum(
    tokenizer: Any,
    system_prompt: str,
    pair: Dict[str, Any],
) -> tinker.Datum:
    """Construct a Tinker training Datum with prompt loss masking."""
    query = pair["user_query"]
    target_resp = pair["target_response"]

    # Optional context cues
    context_parts = []
    if "location" in pair:
        context_parts.append(f"Observer Location: {pair['location']}")
    if "seeing_telemetry" in pair:
        tel = pair["seeing_telemetry"]
        context_parts.append(f"Seeing Score: {tel.get('score', 7.0)}/10 (Class {tel.get('antoniadi_class', 'II')}, Dew Risk: {tel.get('dew_risk', 'low')})")
    if "target_body" in pair:
        tb = pair["target_body"]
        context_parts.append(f"Celestial Object: {tb.get('name', 'Object')}, Altitude: {tb.get('altitude_deg', 30.0)} deg, Cardinal: {tb.get('cardinal', 'East')}")

    context_str = ", ".join(context_parts)
    full_prompt = (
        f"<|im_start|>system\n{system_prompt}\n<|im_end|>\n"
        f"<|im_start|>user\n[Telemetry: {context_str}]\n{query}\n<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    full_completion = f"{target_resp}<|im_end|>"

    prompt_ids = tokenizer.encode(full_prompt)
    completion_ids = tokenizer.encode(full_completion)

    all_ids = prompt_ids + completion_ids

    # Next-token prediction:
    # Model inputs are all_ids[:-1]
    # Targets are all_ids[1:]
    input_tokens = all_ids[:-1]
    target_tokens = all_ids[1:]

    # Mask out prompt: weights=0.0 for prompt tokens, 1.0 for completion tokens
    num_prompt = len(prompt_ids)
    weights = [0.0] * (num_prompt - 1) + [1.0] * len(completion_ids)

    # Ensure lengths match
    if len(weights) != len(target_tokens):
        weights = weights[:len(target_tokens)]
        while len(weights) < len(target_tokens):
            weights.append(1.0)

    return tinker.Datum(
        model_input=tinker.ModelInput.from_ints(input_tokens),
        loss_fn_inputs={
            "target_tokens": tinker.TensorData.from_numpy(np.array(target_tokens, dtype=np.int64)),
            "weights": tinker.TensorData.from_numpy(np.array(weights, dtype=np.float32)),
        }
    )


def run_training_pipeline(
    base_model: str = "Qwen/Qwen3.5-4B",
    rank: int = 16,
    batch_size: int = 5,
    epochs: int = 3,
    learning_rate: float = 1e-4,
) -> Dict[str, Any]:
    """Execute complete LoRA fine-tuning session on Thinking Machines Tinker."""
    api_key = os.getenv("TINKER_API_KEY")
    if not api_key:
        raise ValueError("TINKER_API_KEY environment variable is required")

    print("=================================================================")
    print("      DarkSky Whisper: LoRA Fine-Tuning via Tinker API")
    print("=================================================================")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Base Model: {base_model}")
    print(f"LoRA Rank: {rank}")
    print(f"Batch Size: {batch_size}, Epochs: {epochs}, LR: {learning_rate}")

    # 1. Connect to Tinker Service
    service_client = tinker.ServiceClient(api_key=api_key)
    console_url = service_client.get_console_url()
    print(f"Tinker Console URL: {console_url}")

    # 2. Allocate remote LoRA training actor
    print(f"\n[1/5] Provisioning LoRA training actor for {base_model}...")
    start_time = time.time()
    train_client = service_client.create_lora_training_client(
        base_model=base_model,
        rank=rank,
        train_mlp=True,
        train_attn=True,
    )
    alloc_time = time.time() - start_time
    info = train_client.get_info()
    model_id = getattr(info, "model_id", "unknown")
    print(f"Actor allocated in {alloc_time:.2f}s! Remote Model ID: {model_id}")

    # 3. Load tokenizer and dataset
    print(f"\n[2/5] Loading tokenizer and dataset...")
    tokenizer = train_client.get_tokenizer()
    pairs = load_astronomy_pairs(DATASET_FILE)
    print(f"Loaded {len(pairs)} curated spoken astronomy pairs.")

    datums = [build_datum(tokenizer, SYSTEM_PROMPT, p) for p in pairs]
    print(f"Constructed {len(datums)} training datums with prompt masking.")

    # 4. Training loop
    print(f"\n[3/5] Starting LoRA optimization loop across {epochs} epochs...")
    total_steps = (len(datums) // batch_size) * epochs
    current_step = 0
    epoch_losses = []
    step_history = []

    train_start = time.time()
    for epoch in range(1, epochs + 1):
        print(f"\n--- Epoch {epoch}/{epochs} ---")
        epoch_loss_sum = 0.0
        num_batches = 0

        # Shuffle indices for this epoch
        indices = np.random.permutation(len(datums))

        for i in range(0, len(datums), batch_size):
            batch_indices = indices[i:i + batch_size]
            batch = [datums[idx] for idx in batch_indices]
            if not batch:
                continue

            current_step += 1
            step_start = time.time()

            # Forward-backward gradient computation on Tinker remote GPU
            fwd_future = train_client.forward_backward(batch, loss_fn="cross_entropy")
            fwd_res = fwd_future.result()

            # Extract loss metric
            metrics = getattr(fwd_res, "metrics", {})
            batch_loss = float(metrics.get("loss:sum", 0.0)) / len(batch)
            epoch_loss_sum += batch_loss
            num_batches += 1

            # Optimizer step on LoRA adapter parameters
            opt_future = train_client.optim_step(
                adam_params=tinker.AdamParams(learning_rate=learning_rate)
            )
            opt_future.result()

            step_latency = time.time() - step_start
            step_history.append({
                "step": current_step,
                "epoch": epoch,
                "loss": round(batch_loss, 4),
                "latency_sec": round(step_latency, 3),
            })

            if current_step % 3 == 0 or current_step == total_steps:
                print(f"  Step {current_step:2d}/{total_steps} | Batch Loss: {batch_loss:.4f} | Latency: {step_latency:.2f}s")

        avg_epoch_loss = epoch_loss_sum / max(1, num_batches)
        epoch_losses.append(avg_epoch_loss)
        print(f"--> Epoch {epoch} Average Loss: {avg_epoch_loss:.4f}")

    total_train_time = time.time() - train_start
    print(f"\nOptimization complete in {total_train_time:.2f}s!")
    print(f"Initial Loss: {epoch_losses[0]:.4f} -> Final Loss: {epoch_losses[-1]:.4f}")
    loss_reduction_pct = ((epoch_losses[0] - epoch_losses[-1]) / epoch_losses[0]) * 100.0
    print(f"Loss Reduction: {loss_reduction_pct:.1f}%")

    # 5. Evaluate and sample with fine-tuned weights
    print(f"\n[4/5] Deploying weights to Tinker SamplingClient...")
    sampling_client = train_client.save_weights_and_get_sampling_client(name="darksky-whisper-lora-v1")
    print("Weights deployed to inference endpoint!")

    test_queries = [
        ("How clear is the sky tonight?", "Location: Cherry Springs, Seeing: 8.8/10, Dew: low"),
        ("What is that bright orange beacon rising in the east?", "Object: Aldebaran, Altitude: 24 deg, Cardinal: East"),
    ]

    samples_generated = []
    print(f"\n[5/5] Generating zero-markdown spoken samples from fine-tuned adapter:")
    for query, ctx in test_queries:
        test_prompt_str = (
            f"<|im_start|>system\n{SYSTEM_PROMPT}\n<|im_end|>\n"
            f"<|im_start|>user\n[Telemetry: {ctx}]\n{query}\n<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        test_prompt_tokens = tokenizer.encode(test_prompt_str)

        sample_future = sampling_client.sample(
            prompt=tinker.ModelInput.from_ints(test_prompt_tokens),
            num_samples=1,
            sampling_params=tinker.SamplingParams(
                max_tokens=50,
                temperature=0.7,
                top_p=0.9,
            ),
        )
        sample_res = sample_future.result()

        generated_tokens = []
        if sample_res.sequences:
            seq = sample_res.sequences[0]
            if seq.tokens_np is not None:
                generated_tokens = list(seq.tokens_np)
            elif seq._tokens_list:
                generated_tokens = seq._tokens_list

        generated_text = tokenizer.decode(generated_tokens) if generated_tokens else "(Empty generation)"
        # Clean special tokens
        for stop_token in ["<|im_end|>", "<|endoftext|>"]:
            generated_text = generated_text.replace(stop_token, "")
        generated_text = generated_text.strip()

        print(f"\nQuery: '{query}'")
        print(f"Whisper Spoken Output: \"{generated_text}\"")
        samples_generated.append({
            "query": query,
            "context": ctx,
            "generated_speech": generated_text,
            "word_count": len(generated_text.split()),
        })

    # Save comprehensive report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "Thinking Machines Tinker API",
        "console_url": console_url,
        "remote_model_id": model_id,
        "base_model": base_model,
        "lora_rank": rank,
        "dataset_size": len(pairs),
        "epochs": epochs,
        "batch_size": batch_size,
        "total_steps": current_step,
        "total_train_time_sec": round(total_train_time, 2),
        "initial_loss": round(epoch_losses[0], 4),
        "final_loss": round(epoch_losses[-1], 4),
        "loss_reduction_pct": round(loss_reduction_pct, 2),
        "epoch_losses": [round(l, 4) for l in epoch_losses],
        "step_history": step_history,
        "sample_evaluations": samples_generated,
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nTraining report saved to: {REPORT_FILE}")

    return report


if __name__ == "__main__":
    run_training_pipeline()
