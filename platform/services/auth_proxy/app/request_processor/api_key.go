// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"bytes"
	"crypto/sha512"
	"encoding/binary"
	"errors"
	"fmt"
	"hash/crc32"
	"math/big"
	"regexp"
	"strings"
)

const (
	tokenPrefix            = "geti_pat"
	randomPartLen          = 43
	expectedRandomBytesLen = 32
	checksumLen            = 6
)

// AccessTokenHeader is used for X-API-Keys header validation
type AccessTokenHeader struct {
	token, prefix, randomPart, checksum string
}

func (t *AccessTokenHeader) ParseHeaderValue(headerValue string) error {
	if !strings.HasPrefix(headerValue, tokenPrefix) {
		return errors.New("invalid token format: missing prefix")
	}
	parts := strings.Split(headerValue, "_")
	if len(parts) != 4 {
		return errors.New("invalid token format")
	}
	t.prefix = parts[0] + "_" + parts[1]
	t.randomPart = parts[2]
	t.checksum = parts[3]
	t.token = headerValue
	return nil
}

func (t *AccessTokenHeader) IsFormatValid() bool {
	validRandomPart := regexp.MustCompile(fmt.Sprintf("^[a-zA-Z0-9]{%d}$", randomPartLen))
	validChecksum := regexp.MustCompile(fmt.Sprintf("^[a-zA-Z0-9]{%d}$", checksumLen))
	return validRandomPart.MatchString(t.randomPart) && validChecksum.MatchString(t.checksum)
}

func (t *AccessTokenHeader) IsChecksumValid() bool {
	randomBytes, err := parseBase62(t.randomPart)
	if err != nil {
		fmt.Println("invalid random part of the token")
		return false
	}
	// leading zeroes are ignored by parseBase62 - pad the slice to correct length
	if len(randomBytes) < expectedRandomBytesLen {
		zeroes := bytes.Repeat([]byte{0}, expectedRandomBytesLen)
		padding := zeroes[0 : expectedRandomBytesLen-len(randomBytes)]
		randomBytes = append(padding, randomBytes...)
	}
	checksum := crc32.ChecksumIEEE(randomBytes)
	checksumBytes := make([]byte, 4)
	binary.LittleEndian.PutUint32(checksumBytes, checksum)
	base62Checksum := toBase62(checksumBytes)
	calculatedChecksum := leftPadWithZeroes(base62Checksum, checksumLen)
	return calculatedChecksum == t.checksum
}

func (t *AccessTokenHeader) CalculateHash() (string, error) {
	tokenBytes := []byte(t.token)
	sha384Hash := sha512.Sum384(tokenBytes)
	hashInt := new(big.Int)
	hashInt.SetBytes(sha384Hash[:])
	sha384HashBase62 := hashInt.Text(62)
	paddedHash := leftPadWithZeroes(sha384HashBase62, 65)
	return paddedHash, nil
}

func leftPadWithZeroes(str string, length int) string {
	if len(str) >= length {
		return str
	}
	padding := strings.Repeat("0", length-len(str))
	return padding + str
}

func toBase62(bytes []byte) string {
	var i big.Int
	i.SetBytes(bytes[:])
	return i.Text(62)
}

func parseBase62(s string) ([]byte, error) {
	var i big.Int
	_, ok := i.SetString(s, 62)
	if !ok {
		return []byte{}, fmt.Errorf("cannot parse base62: %q", s)
	}
	return i.Bytes(), nil
}
