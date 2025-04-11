// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestToSnakeCase(t *testing.T) {
	inputExpectedTestSet := map[string]string{
		"FieldById":           "field_by_id",
		"fieldById":           "field_by_id",
		"CellID":              "cell_id",
		"cellId":              "cell_id",
		"":                    "",
		"nochariscapped":      "nochariscapped",
		"already_snake_cased": "already_snake_cased",
	}

	for input, expected := range inputExpectedTestSet {
		snakeCased := ToSnakeCase(input)
		assert.Equal(t, expected, snakeCased)
	}
}

func TestToCamelCase(t *testing.T) {
	inputExpectedTestSet := map[string]string{
		"FieldById":           "fieldById",
		"fieldById":           "fieldById",
		"FieldByID":           "fieldById",
		"CellID":              "cellId",
		"cellId":              "cellId",
		"ID":                  "id",
		"Id":                  "id",
		"":                    "",
		"nochariscapped":      "nochariscapped",
		"already_snake_cased": "already_snake_cased",
	}

	for input, expected := range inputExpectedTestSet {
		snakeCased := ToCamelCase(input)
		assert.Equal(t, expected, snakeCased)
	}
}

func TestIsEmailValid(t *testing.T) {
	testCases := []struct {
		email    string
		expected bool
	}{
		{"user@example.com", true},
		{"jan.pawel@gmail.com", true},
		{"name_123~!#$%^&*{}|-=+@sub.domain.com", true},

		{"invalid-email", false},
		{"@missing-username.com", false},
		{"user@invalid domain.com", false},
		{"email@example", false},
		{"Joe <email@example.com>", false},
		{"email@example.com (Joe Smith)", false},
		{"t@s", false},
		{"verylongemailaddressthatsahouldnotpassinthewholeworld@example.com", false},
		{"GoodEmailExample../@intel.com", false},
	}
	for _, testCase := range testCases {
		result := IsEmailValid(testCase.email)
		if result != testCase.expected {
			t.Errorf("For email '%s' expected validation result is '%v', but got '%v'", testCase.email, testCase.expected, result)
		}
	}
}
