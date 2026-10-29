"""Three-step, last-attention-block LoRA compatibility test; never quality training.

Frozen local 4-bit base; rank-4 q/v adapters only. Frozen recurrent layers stay
in eval mode so their inference-only kernel is never differentiated. This does
NOT verify training through gated-delta/recurrent layers or all-layer MLX SFT.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--target-review", type=Path, required=True)
    p.add_argument("--second-review", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or not args.model.is_dir():
        p.error("Require installed local weights and a new output directory")
    prepared = BASE / "artifacts/prepared-v1"
    cases = [json.loads(l) for l in (prepared / "extraction.train.jsonl").read_text().splitlines()]
    cases = sorted(cases, key=lambda c: (len(c["selected_quote"]), c["id"]))[:3]
    reviews = [json.loads(path.read_text()) for path in [args.target_review, args.second_review]]
    assert all(r["status"] == "complete" for r in reviews), "Judge run incomplete"
    for case in cases:
        for report in reviews:
            matching = [r for r in report["rows"] if r["case_id"] == case["id"] and r["kind"].startswith("target_")]
            assert len(matching) == 1 and matching[0]["pass"], "Target did not pass both LLM reviews"
            assert matching[0]["answer"] == case["target"], "Target changed since review"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
    from mlx.utils import tree_flatten, tree_map
    from mlx_lm import load
    from mlx_lm.tuner.trainer import default_loss
    from mlx_lm.tuner.utils import linear_to_lora_layers

    mx.set_memory_limit(14 * 2**30)
    mx.set_cache_limit(128 * 2**20)
    mx.random.seed(0)
    args.output.mkdir(parents=True)
    adapter = args.output / "adapter"
    adapter.mkdir()
    log = {"created": datetime.now(timezone.utc).isoformat(), "status": "preflight",
           "purpose": "compatibility only, not a trained quality candidate", "model": str(args.model.resolve()),
           "protocol_sha256": sha(BASE / "protocol.json"), "script_sha256": sha(Path(__file__)),
           "data_sha256": sha(prepared / "extraction.train.jsonl"),
           "review_sha256": {str(p): sha(p) for p in [args.target_review, args.second_review]},
           "versions": {n: importlib.metadata.version(n) for n in ["mlx", "mlx-lm", "transformers"]},
           "case_ids": [c["id"] for c in cases], "steps": [],
           "settings": {"rank": 4, "scale": 8.0, "dropout": 0.0, "num_layers": 1,
                        "keys": ["self_attn.q_proj", "self_attn.v_proj"], "learning_rate": 1e-5,
                        "seed": 0, "steps": 3, "batch_size": 1, "max_sequence_length": 512,
                        "loss": "assistant-only cross entropy", "gradient_clip_norm": 1.0,
                        "memory_limit_gib": 14},
           "scope": "Single full-attention block only; no recurrent gradients, full-model SFT or quality gain established",
           "evidence_policy": "Compatibility inputs contain only the literal selected training-source quotation; not full extraction tasks",
           "test_tasks_accessed": False}
    destination = args.output / "smoke.json"
    save = lambda: destination.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
    save()
    try:
        # Hash original files, not merely the snapshot name; never write base weights.
        base_hashes = {p.name: sha(p) for p in sorted(args.model.glob("*.safetensors"))}
        assert base_hashes, "No installed weight shards"
        log["base_weight_sha256_before"] = base_hashes
        start = time.perf_counter()
        model, tokenizer = load(str(args.model))
        log["load_seconds"] = time.perf_counter() - start
        assert not model.layers[-1].is_linear, "Expected final full-attention block"
        model.freeze()
        config = {"rank": 4, "scale": 8.0, "dropout": 0.0,
                  "keys": ["self_attn.q_proj", "self_attn.v_proj"]}
        linear_to_lora_layers(model, 1, config)
        model.eval()
        model.layers[-1].train()
        parameters = tree_flatten(model.trainable_parameters())
        assert parameters and all(".31.self_attn." in k and k.endswith(("lora_a", "lora_b")) for k, _ in parameters)
        log["trainable_names"] = [k for k, _ in parameters]
        log["trainable_parameters"] = sum(v.size for _, v in parameters)
        initial = {k: mx.array(v) for k, v in parameters}
        mx.eval(initial)
        optimizer = optim.Adam(learning_rate=1e-5)
        loss_and_grad = nn.value_and_grad(model, default_loss)
        smoke_data = []
        for case in cases:
            # Exact supplied quote, never dev/test text; short by construction, never token truncation.
            evidence = [{"chunk_id": case["selected_chunk_id"], "text": case["selected_quote"]}]
            messages = [{"role": "system", "content": "Quote a method statement only from supplied evidence and cite its chunk ID."},
                        {"role": "user", "content": json.dumps({"question": case["question"], "evidence": evidence})}]
            prefix = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            complete = tokenizer.apply_chat_template(messages + [{"role": "assistant", "content": case["target"]}],
                                                       tokenize=False, enable_thinking=False)
            tokens = tokenizer.encode(complete, add_special_tokens=False)
            prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
            assert tokens[:len(prefix_tokens)] == prefix_tokens, "Chat prefix mismatch; no guessed loss mask"
            assert len(prefix_tokens) < len(tokens) <= 512, "Untruncated sequence budget failed"
            smoke_data.append({"case_id": case["id"], "messages": messages, "target": case["target"],
                               "tokens": tokens, "offset": len(prefix_tokens)})
        (args.output / "smoke-data.json").write_text(json.dumps(smoke_data, indent=2, ensure_ascii=False) + "\n")
        log["status"] = "training"
        save()
        for step, case in enumerate(smoke_data, 1):
            start = time.perf_counter()
            batch = mx.array([case["tokens"]])
            lengths = mx.array([[case["offset"], len(case["tokens"])]])
            (loss, ntoks), gradients = loss_and_grad(model, batch, lengths)
            grad_flat = tree_flatten(gradients)
            mx.eval(loss, ntoks, gradients)
            finite = all(bool(mx.all(mx.isfinite(g)).item()) for _, g in grad_flat)
            grad_norm = math.sqrt(sum(float(mx.sum(g.astype(mx.float32) ** 2).item()) for _, g in grad_flat))
            assert math.isfinite(loss.item()) and finite and grad_norm > 0, "Nonfinite/zero gradient or loss"
            clipped = tree_map(lambda g: g * min(1.0, 1.0 / grad_norm), gradients)
            optimizer.update(model, clipped)
            mx.eval(model.trainable_parameters(), optimizer.state)
            record = {"step": step, "case_id": case["case_id"], "loss": loss.item(),
                      "assistant_tokens": ntoks.item(), "input_tokens": len(case["tokens"]),
                      "finite_gradients": finite, "unclipped_gradient_norm": grad_norm,
                      "seconds": time.perf_counter() - start, "mlx_peak_gib": mx.get_peak_memory()/2**30,
                      "swap": subprocess.check_output(["sysctl", "-n", "vm.swapusage"], text=True).strip()}
            log["steps"].append(record)
            save()
            print(json.dumps(record), flush=True)
            mx.clear_cache()
        differences = {k: float(mx.max(mx.abs(v - initial[k])).item()) for k, v in tree_flatten(model.trainable_parameters())}
        assert max(differences.values()) > 0, "Adapters did not update"
        log["max_abs_adapter_changes"] = differences
        weights = dict(tree_flatten(model.trainable_parameters()))
        mx.save_safetensors(str(adapter / "adapters.safetensors"), weights)
        (adapter / "adapter_config.json").write_text(json.dumps({"fine_tune_type": "lora", "num_layers": 1,
                                                                 "lora_parameters": config}, indent=2) + "\n")
        # Restore all adapters to their initial values, then load the actual on-disk checkpoint.
        model.load_weights(list(initial.items()), strict=False)
        model.load_weights(str(adapter / "adapters.safetensors"), strict=False)
        loaded = dict(tree_flatten(model.trainable_parameters()))
        assert set(weights) == set(loaded)
        assert all(bool(mx.all(v == loaded[k]).item()) for k, v in weights.items()), "Checkpoint reload mismatch"
        model.eval()
        first = smoke_data[0]
        post_loss, _ = default_loss(model, mx.array([first["tokens"]]), mx.array([[first["offset"], len(first["tokens"])]]))
        mx.eval(post_loss)
        assert math.isfinite(post_loss.item())
        log["reloaded_checkpoint_loss"] = post_loss.item()
        log["adapter_sha256"] = sha(adapter / "adapters.safetensors")
        after = {p.name: sha(p) for p in sorted(args.model.glob("*.safetensors"))}
        assert after == base_hashes, "Base weights unexpectedly changed"
        log["base_weight_sha256_after"] = after
        log["base_weights_unchanged"] = True
        log["status"] = "passed"
        save()
        print(json.dumps({"status": "passed", "output": str(args.output), "trainable_parameters": log["trainable_parameters"]}), flush=True)
    except Exception as exc:
        log["status"] = "failed"
        log["error_type"] = type(exc).__name__
        log["error"] = str(exc)
        save()
        raise


if __name__ == "__main__":
    main()
