#!/usr/bin/env python3
#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
import argparse
import logging
import sys
from pathlib import Path

import cv2
from model_api.models import Model

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


def get_image_files(dataset_path: str) -> list[str]:
    """Get list of image files from the dataset directory."""
    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff", "*.tif"]
    test_images: list[str] = []
    test_path = Path(dataset_path)

    for ext in image_extensions:
        test_images.extend(str(p) for p in test_path.glob(ext))
        test_images.extend(str(p) for p in test_path.glob(ext.upper()))

    return test_images


def analyze_model_performance(  # noqa: C901
    model_path,
    test_images,
    device,
    warmup_runs,
    test_runs,
    num_streams=None,
    num_threads=None,
    max_num_requests=0,
    performance_hint=None,
    performance_hint_num_requests=None,
    use_async=False,
    inference_only=False,
):
    """Complete performance analysis example."""

    # Import required components
    import time

    import numpy as np
    from model_api.adapters.openvino_adapter import OpenvinoAdapter, get_user_config
    from openvino import Core

    # Build plugin config
    core = Core()
    plugin_config = get_user_config(
        device,
        num_streams or "1",
        num_threads,
    )

    # Add performance hint if specified
    if performance_hint:
        plugin_config["PERFORMANCE_HINT"] = performance_hint
    if performance_hint_num_requests is not None:
        plugin_config["PERFORMANCE_HINT_NUM_REQUESTS"] = str(performance_hint_num_requests)

    # Create adapter with custom plugin config
    inference_adapter = OpenvinoAdapter(
        core=core,
        model=model_path,
        device=device,
        plugin_config=plugin_config,
        max_num_requests=max_num_requests,
    )
    model = Model.create_model(inference_adapter, preload=True)

    if inference_only:
        # Inference-only mode: use pre-filled random data, no I/O or preprocessing
        print("Benchmarking in inference only mode (inputs filling are not included in measurement loop).")

        # Get input shape and create random data
        # For image models, we need to create a proper image-like array
        input_layer_name = next(iter(model.inputs.keys()))
        input_shape = model.inputs[input_layer_name].shape
        input_precision = model.inputs[input_layer_name].precision
        input_layout = model.inputs[input_layer_name].layout

        print(f"Input: {input_layer_name}, shape: {input_shape}, precision: {input_precision}, layout: {input_layout}")

        # Get actual compiled model input to check for embedded preprocessing
        compiled_inputs = inference_adapter.compiled_model.inputs
        actual_input = compiled_inputs[0]
        actual_partial_shape = actual_input.partial_shape
        actual_layout = str(actual_input.layout) if hasattr(actual_input, "layout") else str(input_layout)

        print(f"Compiled model input partial_shape: {actual_partial_shape}, layout: {actual_layout}")

        # Create random tensor data matching the actual compiled model input
        # If shape has dynamic dimensions, use reasonable defaults
        tensor_shape = []
        for i, dim in enumerate(actual_partial_shape):
            if dim.is_dynamic:
                # Dynamic dimension - use reasonable default
                if i == 0:
                    tensor_shape.append(1)  # Batch
                elif i == 3 and actual_layout == "NHWC":
                    tensor_shape.append(3)  # Channels for NHWC
                else:
                    tensor_shape.append(224)  # Height/Width default
            else:
                tensor_shape.append(dim.get_length())

        print(f"Using tensor shape: {tensor_shape}")

        # Create random tensor data using Generator API
        rng = np.random.default_rng()
        if input_precision == "FP32" or input_precision == "f32":
            random_tensor = rng.standard_normal(tensor_shape).astype(np.float32)
        elif input_precision == "FP16" or input_precision == "f16":
            random_tensor = rng.standard_normal(tensor_shape).astype(np.float16)
        elif input_precision == "U8" or input_precision == "u8":
            random_tensor = rng.integers(0, 256, size=tensor_shape, dtype=np.uint8)
        elif input_precision == "I8" or input_precision == "i8":
            random_tensor = rng.integers(-128, 128, size=tensor_shape, dtype=np.int8)
        else:
            random_tensor = rng.standard_normal(tensor_shape).astype(np.float32)

        # Create dict_data directly without preprocessing
        dict_data = {input_layer_name: random_tensor}

        print(f"Raw tensor shape: {random_tensor.shape}, dtype: {random_tensor.dtype}")

        print("Starting warm-up...")
        # Warm-up using raw inference - bypass model wrapper, use adapter directly
        for _ in range(warmup_runs):
            inference_adapter.infer_sync(dict_data)

        if use_async:
            print(f"Running {test_runs} test inferences (async mode, inference only)...")
            completed_count = [0]  # Use list to allow modification in callback
            first_start_time = [None]
            last_end_time = [None]

            def callback(request, userdata):
                completed_count[0] += 1
                last_end_time[0] = time.perf_counter()

            # Set callback on the inference adapter directly
            inference_adapter.set_callback(callback)

            # Measure from first submission to last completion
            first_start_time[0] = time.perf_counter()

            # Submit all inference requests
            for i in range(test_runs):
                inference_adapter.infer_async(dict_data, i)
                if (i + 1) % 10 == 0:
                    print(f"  Submitted {i + 1}/{test_runs}")

            # Wait for all requests to complete
            print("  Waiting for all requests to complete...")
            inference_adapter.await_all()

            total_duration = (last_end_time[0] - first_start_time[0]) * 1000  # Convert to ms

            print(f"  Completed {completed_count[0]}/{test_runs}")

            # Calculate metrics
            avg_latency = total_duration / test_runs
            throughput = test_runs / (total_duration / 1000)

            print("\n" + "=" * 60)
            print("           🚀 PERFORMANCE METRICS REPORT 🚀           ")
            print("=" * 60)
            print(f"\n📊 Execution Devices: [{device}]")
            print(f"   Count: {test_runs} iterations")
            print(f"   Duration: {total_duration:.2f} ms")
            print("\n📈 Latency:")
            print(f"   Average: {avg_latency:.2f} ms")
            print(f"\n🎯 Throughput: {throughput:.2f} FPS")
            print("=" * 60 + "\n")

        else:
            print(f"Running {test_runs} test inferences (sync mode, inference only)...")
            inference_times = []

            # Measure each inference separately for latency statistics
            for i in range(test_runs):
                start_time = time.perf_counter()
                inference_adapter.infer_sync(dict_data)
                end_time = time.perf_counter()

                inference_times.append((end_time - start_time) * 1000)  # Convert to ms

                if (i + 1) % 10 == 0:
                    print(f"  Completed {i + 1}/{test_runs}")

            # Calculate statistics
            inference_times = np.array(inference_times)
            total_duration = np.sum(inference_times)
            mean_latency = np.mean(inference_times)
            median_latency = np.median(inference_times)
            min_latency = np.min(inference_times)
            max_latency = np.max(inference_times)
            throughput = test_runs / (total_duration / 1000)

            print("\n" + "=" * 60)
            print("           🚀 PERFORMANCE METRICS REPORT 🚀           ")
            print("=" * 60)
            print(f"\n📊 Execution Devices: [{device}]")
            print(f"   Count: {test_runs} iterations")
            print(f"   Duration: {total_duration:.2f} ms")
            print("\n📈 Latency:")
            print(f"   Median:  {median_latency:.2f} ms")
            print(f"   Average: {mean_latency:.2f} ms")
            print(f"   Min:     {min_latency:.2f} ms")
            print(f"   Max:     {max_latency:.2f} ms")
            print(f"\n🎯 Throughput: {throughput:.2f} FPS")
            print("=" * 60 + "\n")

        return None

    # Regular mode with image loading and full preprocessing
    # Load test image
    image = cv2.imread(test_images[0])

    print("Starting warm-up...")
    # Warm-up runs
    for _ in range(warmup_runs):
        model(image)

    # Reset metrics after warm-up
    model.get_performance_metrics().reset()

    if use_async:
        print(f"Running {test_runs} test inferences (async mode)...")
        # Async inference mode - submit all requests concurrently
        results = {}

        def callback(result, userdata):
            results[userdata] = result

        model.set_callback(callback)

        # Submit all inference requests without blocking
        for i, image_path in enumerate(test_images[:test_runs]):
            image = cv2.imread(image_path)
            model.infer_async(image, user_data=i)
            # Log progress
            if (i + 1) % 10 == 0:
                print(f"  Submitted {i + 1}/{test_runs}")

        # Wait for all requests to complete
        print("  Waiting for all requests to complete...")
        model.await_all()
        print(f"  Completed {len(results)}/{test_runs}")
    else:
        print(f"Running {test_runs} test inferences (sync mode)...")
        # Synchronous inference mode - process images sequentially
        for i, image_path in enumerate(test_images[:test_runs]):
            image = cv2.imread(image_path)
            model(image)
            # Log progress
            if (i + 1) % 10 == 0:
                print(f"  Completed {i + 1}/{test_runs}")

    # Analyze results
    metrics = model.get_performance_metrics()
    metrics.log_metrics()

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Benchmark - a model performance analysis with metrics collection")
    parser.add_argument("model_path", help="Path to the model file (.xml)")
    parser.add_argument("dataset_path", help="Path to the dataset directory containing test images")
    parser.add_argument("--device", type=str, default="CPU", help="OpenVINO device to run the model on (default: CPU)")
    parser.add_argument("--warmup-runs", type=int, default=5, help="Number of warmup runs (default: 5)")
    parser.add_argument("--test-runs", type=int, default=100, help="Number of test runs (default: 100)")

    # OpenVINO performance tuning options
    parser.add_argument(
        "--performance-hint",
        type=str,
        choices=["LATENCY", "THROUGHPUT", "CUMULATIVE_THROUGHPUT"],
        help="OpenVINO performance hint (LATENCY, THROUGHPUT, CUMULATIVE_THROUGHPUT)",
    )
    parser.add_argument(
        "--num-streams",
        type=str,
        help="Number of inference streams (e.g., '1', '2', 'NUM_STREAMS_AUTO')",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        help="Number of CPU threads for inference",
    )
    parser.add_argument(
        "--max-num-requests",
        type=int,
        default=0,
        help="Maximum number of infer requests for asynchronous inference (default: 0 = auto)",
    )
    parser.add_argument(
        "--performance-hint-num-requests",
        type=int,
        help="Number of requests for performance hint optimization",
    )
    parser.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        help="Use asynchronous inference mode for concurrent request submission (recommended for THROUGHPUT mode)",
    )
    parser.add_argument(
        "--inference-only",
        action="store_true",
        help="Use inference-only mode with pre-filled random data (no image I/O or preprocessing overhead)",
    )

    # Show help if no arguments are provided
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    model_path = args.model_path
    dataset_path = args.dataset_path

    # Get list of image files from the directory (only needed if not in inference-only mode)
    if not args.inference_only:
        test_images = get_image_files(dataset_path)
        print(f"Found {len(test_images)} images in {dataset_path}")
        if not test_images:
            print("Error: No images found in the dataset directory!")
            exit(1)
    else:
        # Inference-only mode doesn't need actual images
        test_images = None

    analyze_model_performance(
        model_path,
        test_images,
        args.device,
        args.warmup_runs,
        args.test_runs,
        num_streams=args.num_streams,
        num_threads=args.num_threads,
        max_num_requests=args.max_num_requests,
        performance_hint=args.performance_hint,
        performance_hint_num_requests=args.performance_hint_num_requests,
        use_async=args.use_async,
        inference_only=args.inference_only,
    )


if __name__ == "__main__":
    main()
