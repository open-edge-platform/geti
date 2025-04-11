// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package jwk

import (
	"os"
	"testing"
)

func TestFileReaderKeysProvider_PublicKey(t *testing.T) {
	tests := []struct {
		name           string
		envValue       string
		fileContent    string
		expectedError  bool
		expectedOutput []byte
	}{
		{
			name:          "Environment variable not set",
			envValue:      "",
			expectedError: true,
		},
		{
			name:          "File does not exist",
			envValue:      "/non/existent/file",
			expectedError: true,
		},
		{
			name:           "File exists and contains valid data",
			envValue:       "",
			fileContent:    "public key data",
			expectedError:  false,
			expectedOutput: []byte("public key data"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.envValue == "" && tt.fileContent != "" {
				tmpFile, err := os.CreateTemp("", "testfile")
				if err != nil {
					t.Fatalf("Failed to create temp file: %v", err)
				}
				defer os.Remove(tmpFile.Name())

				if _, err := tmpFile.Write([]byte(tt.fileContent)); err != nil {
					t.Fatalf("Failed to write to temp file: %v", err)
				}
				if err := tmpFile.Close(); err != nil {
					t.Fatalf("Failed to close temp file: %v", err)
				}

				tt.envValue = tmpFile.Name()
			}

			os.Setenv("JWT_CERTIFICATE_PUBLIC_KEY_PATH", tt.envValue)
			defer os.Unsetenv("JWT_CERTIFICATE_PUBLIC_KEY_PATH")

			provider := &FileReaderKeysProvider{}
			output, err := provider.PublicKey()

			if (err != nil) != tt.expectedError {
				t.Errorf("Expected error: %v, got: %v", tt.expectedError, err)
			}

			if string(output) != string(tt.expectedOutput) {
				t.Errorf("Expected output: %s, got: %s", tt.expectedOutput, output)
			}
		})
	}
}

func TestFileReaderKeysProvider_PrivateKey(t *testing.T) {
	tests := []struct {
		name           string
		envValue       string
		fileContent    string
		expectedError  bool
		expectedOutput []byte
	}{
		{
			name:          "Environment variable not set",
			envValue:      "",
			expectedError: true,
		},
		{
			name:          "File does not exist",
			envValue:      "/non/existent/file",
			expectedError: true,
		},
		{
			name:           "File exists and contains valid data",
			envValue:       "",
			fileContent:    "private key data",
			expectedError:  false,
			expectedOutput: []byte("private key data"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.envValue == "" && tt.fileContent != "" {
				tmpFile, err := os.CreateTemp("", "testfile")
				if err != nil {
					t.Fatalf("Failed to create temp file: %v", err)
				}
				defer os.Remove(tmpFile.Name())

				if _, err := tmpFile.Write([]byte(tt.fileContent)); err != nil {
					t.Fatalf("Failed to write to temp file: %v", err)
				}
				if err := tmpFile.Close(); err != nil {
					t.Fatalf("Failed to close temp file: %v", err)
				}

				tt.envValue = tmpFile.Name()
			}

			os.Setenv("JWT_CERTIFICATE_PRIVATE_KEY_PATH", tt.envValue)
			defer os.Unsetenv("JWT_CERTIFICATE_PRIVATE_KEY_PATH")

			provider := &FileReaderKeysProvider{}
			output, err := provider.PrivateKey()

			if (err != nil) != tt.expectedError {
				t.Errorf("Expected error: %v, got: %v", tt.expectedError, err)
			}

			if string(output) != string(tt.expectedOutput) {
				t.Errorf("Expected output: %s, got: %s", tt.expectedOutput, output)
			}
		})
	}
}
