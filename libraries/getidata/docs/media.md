# Media Handling

## Lazy Image Loading

For datasets with images on disk, use lazy loading to avoid memory issues:

```python
from getidata.media import LazyImage

class LazySample(Sample):
    image: LazyImage = image_path_field()

# The image is loaded only when accessed
sample = LazySample(image="/path/to/image.jpg")
print(sample.image.path)   # Returns the path string
image_array = sample.image.data  # Loads from disk here
```

You can configure the loading format:

```python
lazy_img = LazyImage("/path/to/image.jpg", format="BGR", channels_first=True)
img_array = lazy_img.data  # Returns (C, H, W) BGR array
```

## Image Caching

The module includes a global LRU cache for loaded images with byte-size limiting (default 256 MB). The cache is managed through the `ImageCache` class:

```python
from getidata import ImageCache

# Set cache to 512 MB
ImageCache.set_size(512 * 1024 * 1024)

# Check current cache usage
print(f"Cached images: {ImageCache.length()}")
print(f"Current size: {ImageCache.get_size()} bytes")
print(f"Max size: {ImageCache.get_max_size()} bytes")

# Get detailed cache info (count, current bytes, max bytes)
info = ImageCache.info()
print(f"Cache: {info['count']} images, {info['current_size'] / 1024 / 1024:.1f} MB used of {info['max_size'] / 1024 / 1024:.1f} MB")

# Clear all cached images
ImageCache.clear()
```

## Video Handling

The module provides comprehensive video support with lazy frame loading:

```python
from getidata.media import LazyVideoFrame, VideoInfo, MediaInfo
from getidata.fields import video_frame_path_field, video_info_field

class VideoSample(Sample):
    frame: LazyVideoFrame = video_frame_path_field()
    video_info: VideoInfo = video_info_field()

# Create a sample with a video frame reference
sample = VideoSample(
    frame=LazyVideoFrame("/path/to/video.mp4", frame_index=100),
    video_info=VideoInfo(
        path="/path/to/video.mp4",
        total_frames=1000,
        fps=30.0,
        width=1920,
        height=1080,
        duration=33.33,
    ),
)

# Access video frame (loaded on demand)
print(sample.frame.video_path)   # "/path/to/video.mp4"
print(sample.frame.frame_index)  # 100
frame_array = sample.frame.data  # Loads frame 100 from video
```

### Video Frame Cache

Similar to images, video frames have their own LRU cache:

```python
from getidata.media import VideoFrameCache

# Set video frame cache to 256 MB
VideoFrameCache.set_size(256 * 1024 * 1024)

# Check current cache usage
info = VideoFrameCache.info()
print(f"Cached frames: {info['count']}")

# Clear video frame cache
VideoFrameCache.clear()
```

### Video Info Extraction

Extract video metadata:

```python
from getidata.media import extract_video_info, clear_video_info_cache

# Extract metadata from a video file
video_info = extract_video_info("/path/to/video.mp4")
print(f"FPS: {video_info.fps}")
print(f"Frame count: {video_info.total_frames}")
print(f"Duration: {video_info.duration} seconds")
print(f"Width: {video_info.width}, Height: {video_info.height}")

# Clear the video info cache
clear_video_info_cache()
```

### Media Path Field

For datasets with mixed images and videos, use `MediaPathField`:

```python
from getidata.media import MediaInfo
from getidata.fields import media_path_field, media_info_field

class MediaSample(Sample):
    media: LazyImage | LazyVideoFrame = media_path_field()
    media_info: MediaInfo = media_info_field()

# Can hold either images or video frames
image_sample = MediaSample(
    media=LazyImage("/path/to/image.jpg"),
    media_info=MediaInfo(width=1920, height=1080),
)

video_sample = MediaSample(
    media=LazyVideoFrame("/path/to/video.mp4", frame_index=0),
    media_info=MediaInfo(
        width=1920,
        height=1080,
        fps=30.0,
        total_frames=1000,
        duration=33.33,
        codec="h264",
        frame_index=0,
        source_path="/path/to/video.mp4",
    ),
)
```

## Memory Management Best Practices

```python
from getidata import ImageCache
from getidata.media import VideoFrameCache

# For memory-constrained environments (e.g., 64 MB)
ImageCache.set_size(64 * 1024 * 1024)

# For fast iteration over the same images (e.g., 1 GB)
ImageCache.set_size(1024 * 1024 * 1024)

# Disable caching entirely
ImageCache.set_size(0)
```
