// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package http

import (
	"net/http"
	"testing"
)

func TestBuildGetiCookie(t *testing.T) {
	tests := []struct {
		name       string
		method     string
		authHeader string
		wantErr    bool
		wantValue  string
		wantMaxAge int
	}{
		{
			name:       "Valid Authorization Header",
			method:     http.MethodPost,
			authHeader: "Bearer token123",
			wantErr:    false,
			wantValue:  "token123",
			wantMaxAge: 0,
		},
		{
			name:       "Missing Authorization Header",
			method:     http.MethodPost,
			authHeader: "",
			wantErr:    true,
		},
		{
			name:       "Invalid Authorization Header Format",
			method:     http.MethodPost,
			authHeader: "Invalid token123",
			wantErr:    true,
		},
		{
			name:       "Delete Method",
			method:     http.MethodDelete,
			authHeader: "Bearer token123",
			wantErr:    false,
			wantValue:  "",
			wantMaxAge: -1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req, err := http.NewRequest(tt.method, "/", nil)
			if err != nil {
				t.Fatalf("Failed to create request: %v", err)
			}
			req.Header.Set("Authorization", tt.authHeader)

			cookie, err := BuildGetiCookie(req)
			if (err != nil) != tt.wantErr {
				t.Errorf("BuildGetiCookie() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr {
				if cookie.Value != tt.wantValue {
					t.Errorf("BuildGetiCookie() value = %v, want %v", cookie.Value, tt.wantValue)
				}
				if cookie.MaxAge != tt.wantMaxAge {
					t.Errorf("BuildGetiCookie() maxAge = %v, want %v", cookie.MaxAge, tt.wantMaxAge)
				}
			}
		})
	}
}

func TestBuildGetiCookieMissingAuthHeader(t *testing.T) {
	req, err := http.NewRequest(http.MethodPost, "/", nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}

	_, err = BuildGetiCookie(req)
	if err == nil {
		t.Error("Expected an error, got nil")
	}
}
