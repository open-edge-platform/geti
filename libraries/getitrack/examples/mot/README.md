# MOT example: track then evaluate

A tiny synthetic sequence (2 objects, 10 frames) for exercising the `getitrack`
CLI end to end. One detection is intentionally dropped (object 2, frame 5) so the
evaluation reports a non-trivial miss.

## Files

- `detections.txt`: input detections in MOT format (`frame,id,x,y,w,h,score,class`, `id` is `-1`).
- `ground_truth.txt`: ground-truth tracks in MOT format (`frame,id,x,y,w,h`).
- `tracks.txt`, `metrics.json`: produced by the commands below.

## Run it

Track over the detections with ByteTrack, writing MOT-format results:

```
getitrack track -d examples/mot/detections.txt -a bytetrack -o examples/mot/tracks.txt
```

Evaluate the predicted tracks against the ground truth:

```
getitrack eval -p examples/mot/tracks.txt -g examples/mot/ground_truth.txt -o examples/mot/metrics.json
```

`eval` needs the optional extra: `pip install "getitrack[eval]"`.

## Expected result

The dropped detection shows up as a single miss: `recall = 0.95`, `num_misses = 1`,
`num_fragmentations = 1`, with `num_switches = 0` and both objects `mostly_tracked`.
