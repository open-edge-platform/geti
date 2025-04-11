// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package jwk

import (
	"auth_proxy/app/utils"
	"crypto/rsa"
	"crypto/sha512"
	"crypto/x509"
	"encoding/base64"
	"encoding/hex"
	"encoding/pem"
	"fmt"
	"math/big"
)

var logger = utils.InitializeBasicLogger()

type JWK struct {
	Kid string `json:"kid"`
	Use string `json:"use"`
	Kty string `json:"kty"`
	N   string `json:"n"`
	E   string `json:"e"`
}

func (j JWK) Equal(other JWK) bool {
	return j.Kid == other.Kid && j.Use == other.Use && j.Kty == other.Kty && j.N == other.N && j.E == other.E
}

func FromPEM(pemBytes []byte) (JWK, error) {
	// Parse the PEM encoded certificate
	block, _ := pem.Decode(pemBytes)
	if block == nil {
		logger.Error("failed to parse PEM block containing the certificate")
		return JWK{}, fmt.Errorf("failed to parse PEM block containing the certificate")
	}

	// Parse the x509 certificate
	cert, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		logger.Errorf("failed to parse certificate: %v", err)
		return JWK{}, fmt.Errorf("failed to parse certificate: %v", err)
	}

	// Ensure the public key is of RSA type
	rsaPubKey, ok := cert.PublicKey.(*rsa.PublicKey)
	if !ok {
		logger.Error("the public key is not of RSA type")
		return JWK{}, fmt.Errorf("the public key is not of RSA type")
	}

	return JWK{
		Kid: CalculateKid(pemBytes),
		Use: "sig",
		Kty: "RSA",
		N:   base64.RawURLEncoding.EncodeToString(rsaPubKey.N.Bytes()),
		E:   base64.RawURLEncoding.EncodeToString(big.NewInt(int64(rsaPubKey.E)).Bytes()),
	}, nil
}

func CalculateKid(pemBytes []byte) string {
	hash := sha512.Sum512(pemBytes)
	return hex.EncodeToString(hash[:])
}
