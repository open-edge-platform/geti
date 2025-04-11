// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestGetFieldNames(t *testing.T) {
	type FakeStruct struct {
		Country   string
		Location  string
		Type      *string
		CellID    int
		Valid     bool
		CreatedAt time.Time
	}

	expectedFields := []string{
		"Country", "Location", "Type", "CellID", "Valid", "CreatedAt",
	}

	fieldNames := GetFieldNames(FakeStruct{})
	assert.Equal(t, expectedFields, fieldNames)
}

func TestGetFieldNamesEmptyStruct(t *testing.T) {
	type EmptyStruct struct{}

	emptyFields := GetFieldNames(EmptyStruct{})
	assert.Equal(t, emptyFields, []string{})
}
