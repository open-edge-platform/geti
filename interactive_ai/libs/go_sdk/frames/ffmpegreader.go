// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package frames

import (
	"bytes"
	"fmt"
	"strconv"

	ffmpeg "github.com/u2takey/ffmpeg-go"
)

// FrameReader provides methods to read a single frame
type FrameReader interface {
	ReadFrameToBuffer(path string, frameNum int) (*bytes.Buffer, error)
	ReadFrameToBufferFps(path string, frameNum int, fps float64) (*bytes.Buffer, error)
}

type FramerReaderImpl struct {
}

// ReadFrameToBuffer Reads a frame from a video into memory
func (s FramerReaderImpl) ReadFrameToBuffer(path string, frameNum int) (*bytes.Buffer, error) {
	buf := bytes.NewBuffer(nil)
	err := ffmpeg.Input(path).
		Filter("select", ffmpeg.Args{fmt.Sprintf("eq(n,%d)", frameNum)}).
		Output("pipe:", ffmpeg.KwArgs{"vframes": 1, "format": "image2", "vcodec": "mjpeg"}).
		WithOutput(buf).
		Run()
	if err != nil {
		return nil, err
	}
	return buf, nil
}

// ReadFrameToBufferFps Reads a frame from a video into memory. FPS is used to determine at which timestamp the video should
// be loaded to speed up frame reading. If FPS is 0 or negative, it fallbacks to non-optimised version of frame extraction
func (s FramerReaderImpl) ReadFrameToBufferFps(path string, frameNum int, fps float64) (*bytes.Buffer, error) {
	if fps <= 0 {
		return s.ReadFrameToBuffer(path, frameNum)
	}
	// Convert FPS to millisecond timestamp at which the video should be loaded in
	milliSeconds := int((float64(frameNum) / fps) * 1000)
	msString := strconv.Itoa(milliSeconds) + "ms"

	buf := bytes.NewBuffer(nil)
	err := ffmpeg.Input(path, ffmpeg.KwArgs{"ss": msString}).
		Filter("select", ffmpeg.Args{"eq(n,0)"}).
		Output("pipe:", ffmpeg.KwArgs{"vframes": 1, "format": "image2", "vcodec": "mjpeg", "q:v": "20"}).
		Silent(true).
		WithOutput(buf).
		Run()
	if err != nil {
		return nil, err
	}
	return buf, nil
}
