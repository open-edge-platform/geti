// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"encoding/json"
	"fmt"
	"github.com/golang-jwt/jwt/v5"
	"math"
	"math/rand"
	"regexp"
	"time"
)

func (h *RequestHandler) ExtractOrgIDFromPath() string {
	re := regexp.MustCompile("/organizations/([a-zA-Z0-9-]+)")
	matches := re.FindStringSubmatch(h.RequestPath)
	if len(matches) != 2 {
		h.Logger.Debugf("no organization ID found in the URL: %s", h.RequestPath)
		return ""
	}
	return matches[1]
}

func GenerateRandomString(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	b := make([]byte, n)
	for i := range b {
		b[i] = letters[r.Intn(len(letters))]
	}
	return string(b)
}

func GetAuthenticationTime(claims jwt.MapClaims) (time.Time, error) {
	authTimeClaim, ok := claims["auth_time"]
	if !ok {
		return time.Time{}, fmt.Errorf("authentication time claim not found")
	}
	switch exp := authTimeClaim.(type) {
	case float64:
		return GetDateFromSeconds(exp), nil
	case json.Number:
		v, _ := exp.Float64()
		return GetDateFromSeconds(v), nil
	}

	return time.Time{}, fmt.Errorf("authentication time claim has invalid type")
}

func GetDateFromSeconds(f float64) time.Time {
	round, frac := math.Modf(f)
	return time.Unix(int64(round), int64(frac*1e9))
}
