#!/usr/bin/env python3
"""Benchmark RF-DETR-Seg-XL training to compare PyTorch versions on XPU.

Usage:
    uv run python benchmark_torch_compare.py
    uv run python benchmark_torch_compare.py --epochs 3 --device cpu
"""

import argparse
import sys
import time
import torch


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark RF-DETR-Seg-XL")
    parser.add_argument("--device", default="xpu", choices=["cpu", "xpu", "cuda"])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"PyTorch version : {torch.__version__}")
    print(f"Device          : {args.device}")
    print(f"Num epochs      : {args.epochs}")
    print(f"Batch size      : 4  (recipe default)")
    print(f"Dataset         : data/wgisd")
    print(f"Model           : rfdetr_seg_xlarge")

    if args.device == "xpu" and not torch.xpu.is_available():
        sys.exit("ERROR: XPU not available. Try --device cpu.")
    if args.device == "cuda" and not torch.cuda.is_available():
        sys.exit("ERROR: CUDA not available. Try --device cpu.")

    from getitune.engine import create_engine

    t0 = time.monotonic()
    engine = create_engine(
        model="rfdetr_seg_xlarge",
        data="data/wgisd",
        work_dir=f"./benchmark_tmp_{args.device}",
        device=args.device,
    )
    t1 = time.monotonic()
    print(f"Engine init     : {t1 - t0:.1f}s")
    print()

    engine.train(
        max_epochs=args.epochs,
        seed=args.seed,
        precision="16-mixed",
        num_sanity_val_steps=0,
        gradient_clip_val=0.1,
    )

    t2 = time.monotonic()
    dt = t2 - t1
    print(f"\nTotal train    : {dt:.1f}s")
    print(f"Per-epoch      : {dt / args.epochs:.1f}s")


if __name__ == "__main__":
    main()
