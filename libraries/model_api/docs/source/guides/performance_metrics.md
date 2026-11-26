# Performance Metrics

The Model API provides comprehensive performance monitoring capabilities through the `PerformanceMetrics` class. This allows to measure and analyze the performance of model inference pipeline, including detailed timing information for each stage of the inference process.

## Overview

Performance metrics are automatically collected during model inference and include information for:

- **Model loading time**: Time spent loading the model to the inference device
- **Preprocessing time**: Time spent on input data preprocessing
- **Inference time**: Time spent on actual model inference on the device
- **Postprocessing time**: Time spent on output data postprocessing
- **Total time**: Overall time for the complete inference pipeline
- **Total minimal time**: Overall minimum time for the complete inference pipeline
- **Total maxmium time**: Overall maximum time for the complete inference pipeline
- **Total frames**: Total number of inferences
- **FPS**: Frames Per Second

All timing statistics are reported in milliseconds (ms).

Each metric provides statistical information including mean, standard deviation, and individual measurements.

## Basic Usage

### Accessing Performance Metrics

Every model instance automatically collects performance metrics. You can access them using the `get_performance_metrics()` method:

```python
from model_api.models import Model
import cv2

# Create a model
model = Model.create_model("path/to/your/model.xml")

# Perform inference
image = cv2.imread("path/to/image.jpg")
result = model(image)

# Get performance metrics
metrics = model.get_performance_metrics()
```

### Logging Performance Metrics

The simplest way to view performance metrics is to use the built-in logging method:

```python
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Log all performance metrics to console
metrics.log_metrics()
```

This will output detailed performance information:

```bash
============================================================
               🚀 PERFORMANCE METRICS REPORT 🚀
============================================================

📊 Model Loading:
    Load Time: 2497.00 ms

⚙️  Processing Times (mean ± std):
    Preprocess:  1.00 ms ± 0.10 ms
    Inference:   570.00 ms ± 20.00 ms
    Postprocess: 1.00 ms ± 0.10 ms

📈 Total Time Statistics:
    Mean:  572.00 ms ± 20.00 ms
    Min:   556.00 ms
    Max:   642.00 ms

🎯 Performance Summary:
    Total Frames: 100
    FPS:          1.75
============================================================
```

## Detailed Metrics Access

### Individual Timing Statistics

You can access individual timing statistics for more detailed analysis:

```python
# Get specific timing statistics
load_time = metrics.get_load_time()
preprocess_time = metrics.get_preprocess_time()
inference_time = metrics.get_inference_time()
postprocess_time = metrics.get_postprocess_time()
total_time = metrics.get_total_time()
total_min_time = metrics.get_total_time_min()
total_max_time = metrics.get_total_time_max()

# Access statistical information
print(f"Mean inference time: {inference_time.mean():.2f} ms")
print(f"Standard deviation: {inference_time.stddev():.2f} ms")
print(f"Total inference time: {inference_time.time:.2f} ms")
print(f"Number of inferences: {inference_time.count}")
```

### Frame Rate and Throughput

```python
# Get frames per second and total frame count
fps = metrics.get_fps()
total_frames = metrics.get_total_frames()

print(f"Processed {total_frames} frames at {fps:.2f} FPS")
```

## Advanced Usage

### Batch Processing Performance

When processing multiple inputs, performance metrics accumulate across all inferences:

```python
import cv2
from model_api.models import DetectionModel

model = DetectionModel.create_model("path/to/detection/model.xml")

# Process multiple images
images = ["image1.jpg", "image2.jpg", "image3.jpg"]
for image_path in images:
    image = cv2.imread(image_path)
    result = model(image)

# Get accumulated metrics for all inferences
metrics = model.get_performance_metrics()
metrics.log_metrics()
```

### Performance Monitoring During Inference

```python
import cv2
from model_api.models import ClassificationModel

model = ClassificationModel.create_model("efficientnet-b0-pytorch")
image = cv2.imread("test_image.jpg")

# Run multiple inferences and monitor performance
for i in range(100):
    result = model(image)

    # Check performance every 10 inferences
    if (i + 1) % 10 == 0:
        metrics = model.get_performance_metrics()
        print(f"After {i + 1} inferences:")
        print(f"  Mean inference time: {metrics.get_inference_time().mean():.2f} ms")
        print(f"  Current FPS: {metrics.get_fps():.2f}")
```

## Performance Optimization Tips

### Analyzing Bottlenecks

Use performance metrics to identify bottlenecks in inference pipeline:

```python
metrics = model.get_performance_metrics()

preprocess_time = metrics.get_preprocess_time().mean()
inference_time = metrics.get_inference_time().mean()
postprocess_time = metrics.get_postprocess_time().mean()
total = preprocess_time + inference_time + postprocess_time

print("Time breakdown:")
print(f"  Preprocessing: {preprocess_time:.2f} ms ({preprocess_time/total:.1%})")
print(f"  Inference:     {inference_time:.2f} ms ({inference_time/total:.1%})")
print(f"  Postprocessing: {postprocess_time:.2f} ms ({postprocess_time/total:.1%})")
```

### Warm-up Considerations

The first few inferences may be slower due to system warm-up. Consider excluding them from performance analysis:

```python
# Warm-up inferences
for _ in range(5):
    model(image)

# Reset metrics after warm-up (load time stats are preserved by default)
metrics = model.get_performance_metrics()
metrics.reset()

# If you also need to clear model load measurements
# metrics.reset(include_load_time=True)

# Now measure actual performance
for _ in range(100):
    model(image)

metrics = model.get_performance_metrics()
metrics.log_metrics()
```

## Best Practices

1. **Warm-up Period**: Always include a warm-up period before measuring performance for production benchmarks.

2. **Multiple Runs**: Collect metrics over multiple inference runs to get statistically significant results.

3. **Reset Between Tests**: Reset metrics when comparing different configurations or models.

4. **Monitor All Stages**: Pay attention to all pipeline stages (preprocessing, inference, postprocessing) to identify bottlenecks.

5. **Environment Consistency**: Ensure consistent testing conditions (device state, background processes, etc.) when comparing performance.

## Example: Complete Performance Analysis

```python
import cv2
from model_api.models import DetectionModel

def analyze_model_performance(model_path, test_images, warmup_runs=5, test_runs=100):
    """Complete performance analysis example."""

    # Load model
    model = DetectionModel.create_model(model_path)

    # Load test image
    image = cv2.imread(test_images[0])

    print("Starting warm-up...")
    # Warm-up runs
    for _ in range(warmup_runs):
        model(image)

    # Reset metrics after warm-up (keeping load time by default)
    metrics = model.get_performance_metrics()
    metrics.reset()

    print(f"Running {test_runs} test inferences...")
    # Performance measurement runs
    for i, image_path in enumerate(test_images[:test_runs]):
        image = cv2.imread(image_path)
        result = model(image)

        # Log progress
        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{test_runs}")

    # Analyze results
    metrics = model.get_performance_metrics()

    print("\n" + "="*50)
    print("PERFORMANCE ANALYSIS RESULTS")
    print("="*50)

    metrics.log_metrics()

    # Additional analysis
    inference_time = metrics.get_inference_time()
    print(f"\nInference time analysis:")
    print(f"  Minimum: {min(inference_time.durations):.2f} ms")
    print(f"  Maximum: {max(inference_time.durations):.2f} ms")
    print(
        f"  Median: {sorted(inference_time.durations)[len(inference_time.durations)//2]:.2f} ms"
    )

    return metrics

# Usage
if __name__ == "__main__":
    model_path = "path/to/your/model.xml"
    test_images = ["image1.jpg", "image2.jpg", "image3.jpg"]  # Add more images

    metrics = analyze_model_performance(model_path, test_images)
```

This comprehensive performance monitoring system helps optimize model inference pipeline and ensure optimal performance in production deployments.
