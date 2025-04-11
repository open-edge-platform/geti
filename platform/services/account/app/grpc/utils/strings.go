// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"regexp"
	"strings"
	"unicode"
	"unicode/utf8"
)

var reCap = regexp.MustCompile("([a-z0-9])([A-Z])")

func ToSnakeCase(camelCase string) (result string) {
	result = reCap.ReplaceAllString(camelCase, "${1}_${2}")
	result = strings.ToLower(result)
	return
}

func ToCamelCase(pascalCase string) (result string) {
	pascalCaseRune, size := utf8.DecodeRuneInString(pascalCase)
	if pascalCaseRune == utf8.RuneError {
		return pascalCase
	}

	edgeCases := map[string]string{
		"CellID":    "cellId",
		"FieldByID": "fieldById",
		"ID":        "id",
		"Id":        "id",
	}
	// Check if the input string is an edge case
	if camel, ok := edgeCases[pascalCase]; ok {
		return camel
	}

	lowerRune := unicode.ToLower(pascalCaseRune)
	return string(lowerRune) + pascalCase[size:]
}

func IsEmailValid(email string) bool {
	if len(email) < 5 || len(email) > 64 {
		return false
	}
	validFormat := regexp.MustCompile("^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@" +
		"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$")
	return validFormat.MatchString(email)
}

func Contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
