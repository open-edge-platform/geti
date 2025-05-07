// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package frames

import (
	"bufio"
	"bytes"
	"context"
	"fmt"
	"io"

	ffmpeg "github.com/u2takey/ffmpeg-go"
	"go.opentelemetry.io/otel/attribute"

	"geti.com/iai_core/entities"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/telemetry"
)

type CLIFrameExtractor interface {
	Start(ctx context.Context, video *entities.Video, start, end, skip int, writer io.WriteCloser) <-chan error
	Read(ctx context.Context, pr io.ReadCloser) <-chan *FrameData
}

type FFmpegCLIFrameExtractor struct {
}

type FrameData struct {
	Index int
	Data  []byte
}

func (s *FFmpegCLIFrameExtractor) Start(ctx context.Context, video *entities.Video, start, end, skip int, writer io.WriteCloser) <-chan error {
	logger.TracingLog(ctx).Infof("Starting frame extraction process for %q, frames requested start=%d, end=%d, "+
		"skip=%d, video fps %g...", video.FilePath, start, end, skip, video.FPS)
	done := make(chan error)
	go func() {
		_, span := telemetry.Tracer().Start(ctx, "ffmpeg-extract-frames")
		defer span.End()

		// Convert FPS to millisecond timestamp at which the video should be loaded in
		inputFlags := ffmpeg.KwArgs{
			"ss": fmt.Sprintf("%dms", int((float64(start)/video.FPS)*1000)),
		}

		// Account for case where batch is smaller than frame skip which combined with vf FPS filter can mean that no
		// frame is selected within the range. In this case, we set vf FPS to the videos FPS to select the start frame.
		vfFps := video.FPS / float64(skip)
		if float64(end-start) < vfFps {
			vfFps = video.FPS
		}

		// Building select filter:
		// vf: The skip is converted to the amount of frames per second that need to be extracted. This is done to
		// account for the fact that the video may have a variable frame rate.
		// CRITICAL: Use JPEG quality factor matching OpenCV's default (95) for consistency.
		// OpenCV quality 95 ≈ FFmpeg -q:v 2. Compression artifacts from different quality settings
		// can alter pixel values and lead to inconsistent model predictions across processing paths.
		outputFlags := ffmpeg.KwArgs{
			"vf":       fmt.Sprintf("fps=%f", vfFps),
			"vsync":    "vfr",        // video sync for variable frame rate
			"f":        "image2pipe", // outputs to a pipe
			"c:v":      "mjpeg",
			"frames:v": (end-start)/skip + 1, // limit number of frames to extract
			"an":       "",                   // disable audio processing
		}

		// -format=image2pipe since it outputs frame bytes into pipe writer passed in params
		err := ffmpeg.Input(video.FilePath, inputFlags).
			Output("pipe:", outputFlags).
			WithOutput(writer).
			Silent(true).
			Run()

		_ = writer.Close()
		done <- err
		close(done)
	}()
	return done
}

var (
	jpegStartMarker = []byte{0xFF, 0xD8}
	jpegEndMarker   = []byte{0xFF, 0xD9}
)

// Read reads frame bytes from the provided pipe reader.
// It continuously reads from the pipe and processes the data to detect complete JPEG frames.
// When a complete JPEG frame is detected, it extracts the frame bytes and sends them as a byte slice to the output channel.
// A JPEG frame is identified by the start marker (0xFFD8) and end marker (0xFFD9).
// The function ensures that each detected JPEG frame is properly formed before sending it to the output channel.
func (s *FFmpegCLIFrameExtractor) Read(ctx context.Context, pr io.ReadCloser) <-chan *FrameData {
	frameCh := make(chan *FrameData)

	go func() {
		_, span := telemetry.Tracer().Start(ctx, "ffmpeg-read-frames")
		defer span.End()

		defer func() {
			_ = pr.Close()
			close(frameCh)
		}()

		reader := bufio.NewReader(pr)
		cnt := 0
		for {
			_, err := reader.ReadBytes(jpegStartMarker[0])
			if err == io.EOF {
				break
			}
			if err != nil {
				logger.TracingLog(ctx).Errorf("Error reading from pipe: %s", err)
				break
			}

			var jpegBuffer bytes.Buffer
			jpegBuffer.Write([]byte{jpegStartMarker[0]})

			for {
				b, err := reader.ReadByte()
				if err != nil {
					logger.TracingLog(ctx).Errorf("Error reading JPEG data %s", err)
					break
				}
				jpegBuffer.WriteByte(b)
				if jpegBuffer.Len() >= 2 && bytes.HasSuffix(jpegBuffer.Bytes(), jpegEndMarker) {
					break
				}
			}
			frameCh <- &FrameData{
				Index: cnt,
				Data:  jpegBuffer.Bytes(),
			}
			cnt++
		}
		span.SetAttributes(attribute.Int("frames", cnt))
	}()

	return frameCh
}
