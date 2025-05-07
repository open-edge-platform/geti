// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package entities

// ObjectMetadata captures the subset of object metadata that can be used in upstream layers.
type ObjectMetadata struct {
	Size        int64
	ContentType string
}

func NewObjectMetadata(size int64, contentType string) *ObjectMetadata {
	return &ObjectMetadata{
		Size:        size,
		ContentType: contentType,
	}
}
