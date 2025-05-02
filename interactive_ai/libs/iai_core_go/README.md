# go_sdk

## Frame extraction benchmarks

### Setup

#### Video params

| name                 | size    | resolution  | duration | fps |
|:---------------------|:--------|:------------|:---------|:----|
| GoPro Side Mount Pt1 | 2.5GB   | 1920x1080   | 1005s    | 30  |
| cars_on_highway      | 47.38MB | 1920x1080   | 60s      | 50  |

#### Steps

1. Videos are uploaded to local Minio service
2. Presigned URLs are generated for the uploaded videos
3. [Benchmarks](frames/extractors_test.go) are executed with a specific set of parameters, as defined below

#### Benchmarks:

```bash
// GoPro Side Mount Pt1 (from=29000 to=29199 skip=10)

❯ go test -bench=. -benchmem -run=^# -count=3
goos: darwin
goarch: arm64
pkg: geti.com/iai_core/frames
BenchmarkExtractFramesCLI-12               1        12328635291 ns/op        6103320 B/op      10414 allocs/op
BenchmarkExtractFramesCLI-12               1        18724692875 ns/op        6105944 B/op      10414 allocs/op
BenchmarkExtractFramesCLI-12               1        18397338208 ns/op        6103760 B/op      10412 allocs/op
BenchmarkExtractFramesCLIPipe-12           1        4117262709 ns/op         4130448 B/op        562 allocs/op
BenchmarkExtractFramesCLIPipe-12           1        2252185542 ns/op         4129840 B/op        563 allocs/op
BenchmarkExtractFramesCLIPipe-12           1        1763844250 ns/op         4130976 B/op        562 allocs/op
BenchmarkExtractFramesOpenCV-12            1        1316969167 ns/op         1812872 B/op         59 allocs/op
BenchmarkExtractFramesOpenCV-12            1        1276417583 ns/op         1812856 B/op         59 allocs/op
BenchmarkExtractFramesOpenCV-12            1        1282678417 ns/op         1812856 B/op         59 allocs/op
PASS
ok      geti.com/iai_core/frames  63.453s


// cars_on_highway (from=0 to=199 skip=10)

❯ go test -bench=. -benchmem -run=^# -count=3
goos: darwin
goarch: arm64
pkg: geti.com/iai_core/frames
BenchmarkExtractFramesCLI-12               1        2914159167 ns/op         6100736 B/op      10417 allocs/op
BenchmarkExtractFramesCLI-12               1        2557185500 ns/op         6099112 B/op      10403 allocs/op
BenchmarkExtractFramesCLI-12               1        2590927750 ns/op         6099656 B/op      10407 allocs/op
BenchmarkExtractFramesCLIPipe-12           1        1732288625 ns/op         4130160 B/op        563 allocs/op
BenchmarkExtractFramesCLIPipe-12           1        1745238041 ns/op         4129416 B/op        560 allocs/op
BenchmarkExtractFramesCLIPipe-12           1        1744677542 ns/op         4130968 B/op        568 allocs/op
BenchmarkExtractFramesOpenCV-12            1        1227962000 ns/op         2280104 B/op         58 allocs/op
BenchmarkExtractFramesOpenCV-12            1        1212712625 ns/op         2280120 B/op         58 allocs/op
BenchmarkExtractFramesOpenCV-12            1        1221355542 ns/op         2279656 B/op         57 allocs/op
PASS
ok      geti.com/iai_core/frames  19.093s

// GoPro Side Mount Pt1 (from=29000 to=29199 skip=10)

❯ go test -bench=. -benchmem -run=^# -count=3
goos: darwin
goarch: arm64
pkg: geti.com/iai_core/frames
BenchmarkExtractFramesOpenCV-12             1        1213358250 ns/op         1814008 B/op         64 allocs/op
BenchmarkExtractFramesOpenCV-12             1        1207513625 ns/op         1813400 B/op         61 allocs/op
BenchmarkExtractFramesOpenCV-12             1        1207162666 ns/op         1812856 B/op         59 allocs/op
BenchmarkExtractFramesLibav-12              2         806099562 ns/op         5254808 B/op        318 allocs/op
BenchmarkExtractFramesLibav-12              2         838948770 ns/op         5254820 B/op        319 allocs/op
BenchmarkExtractFramesLibav-12              2         855009666 ns/op         5254816 B/op        318 allocs/op
PASS
ok      geti.com/iai_core/frames  12.013s

```
