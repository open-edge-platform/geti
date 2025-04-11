// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package jwk

import (
	"auth_proxy/app/utils"
	"fmt"
	"os"
)

// KeyProvider is an interface for getting PEM encoded keys.
type KeyProvider interface {
	PrivateKey() ([]byte, error)
	PublicKey() ([]byte, error)
}

// FileReaderKeysProvider is an implementation of KeyProvider that reads keys from files.
type FileReaderKeysProvider struct{}

// PrivateKey reads the private key from the specified file location.
func (f *FileReaderKeysProvider) PrivateKey() ([]byte, error) {
	return f.readFile("JWT_CERTIFICATE_PRIVATE_KEY_PATH")
}

// PublicKey reads the public key from the specified file location.
func (f *FileReaderKeysProvider) PublicKey() ([]byte, error) {
	return f.readFile("JWT_CERTIFICATE_PUBLIC_KEY_PATH")
}

func (f *FileReaderKeysProvider) readFile(envName string) ([]byte, error) {
	fileLocation := utils.GetEnv(envName, "")
	if fileLocation == "" {
		return nil, fmt.Errorf("environment variable %s is not set", envName)
	}

	key, err := os.ReadFile(fileLocation)
	if err != nil {
		return nil, fmt.Errorf("failed to read key from file %s: %v", fileLocation, err)
	}

	return key, nil
}
