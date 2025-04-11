// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"auth_proxy/app/jwk"
	"crypto"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"errors"
	"fmt"
	"github.com/golang-jwt/jwt/v5"
)

func GetKeyId(verificationKey []byte) string {
	hash := crypto.SHA512.New()
	hash.Write(verificationKey)
	return fmt.Sprintf("%x", hash.Sum(nil))
}

func ParseJwtString(tokenString string) (*jwt.Token, jwt.MapClaims, error) {
	claims := jwt.MapClaims{}
	token, err := jwt.ParseWithClaims(
		tokenString,
		claims,
		KeyFunc,
	)
	// Perform signature verification here. Currently invalid signature errors are ignored.
	if err != nil && !errors.Is(err, jwt.ErrTokenSignatureInvalid) {
		return &jwt.Token{}, jwt.MapClaims{}, err
	}

	return token, claims, nil
}

func KeyFunc(*jwt.Token) (interface{}, error) {
	// This function shall return the verification key for the external JWT,
	// if signature verification is needed in the future.
	return []byte("External JWT verification key placeholder"), nil
}

func PrivateKeyFromPem(privateKeyPem []byte) (*rsa.PrivateKey, error) {
	block, _ := pem.Decode(privateKeyPem)
	if block == nil {
		return nil, errors.New("failed to parse PEM block containing the privateKey")
	}

	privateKey, err := x509.ParsePKCS8PrivateKey(block.Bytes)
	if err != nil {
		return nil, err
	}

	return privateKey.(*rsa.PrivateKey), nil
}

func GetKeys() (*rsa.PrivateKey, []byte, error) {
	provider := &jwk.FileReaderKeysProvider{}
	publicKey, err := provider.PublicKey()
	if err != nil {
		return nil, nil, fmt.Errorf("failed to get public key: %v", err)
	}

	privateKey, err := provider.PrivateKey()
	if err != nil {
		return nil, nil, fmt.Errorf("failed to get private key: %v", err)
	}

	rsaPrivateKey, err := PrivateKeyFromPem(privateKey)
	if err != nil {
		return nil, nil, fmt.Errorf("unknown error occurred while parsing the private key: %+v", err)
	}

	return rsaPrivateKey, publicKey, nil
}
