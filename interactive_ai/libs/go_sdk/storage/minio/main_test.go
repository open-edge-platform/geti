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

package minio

import (
	"context"
	"log"
	"os"
	"testing"

	"geti.com/go_sdk/testhelper"
)

func TestMain(m *testing.M) {
	ctx := context.Background()
	container, err := testhelper.StartMinioContainer(ctx)
	if err != nil {
		log.Fatalf("Cannot start minio container: %s", container)
	}

	code := m.Run()

	if err := testhelper.StopMinioContainer(ctx, container); err != nil {
		log.Fatalf("Failed to terminate container: %v", err)
	}

	os.Exit(code)
}
