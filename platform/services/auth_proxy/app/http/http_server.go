// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package http

import (
	"auth_proxy/app/jwk"
	"auth_proxy/app/utils"
	"io"
	"net/http"
)

var logger = utils.InitializeBasicLogger()

type loggingResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func newLoggingResponseWriter(w http.ResponseWriter) *loggingResponseWriter {
	return &loggingResponseWriter{w, http.StatusOK}
}

func (lrw *loggingResponseWriter) WriteHeader(code int) {
	lrw.statusCode = code
	lrw.ResponseWriter.WriteHeader(code)
}

func logRequestMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		lrw := newLoggingResponseWriter(w)
		next.ServeHTTP(lrw, r)
		logger.Infof("Accessed route: %s %s, Response status: %d", r.Method, r.URL.Path, lrw.statusCode)
	})
}

func handleKeys(w http.ResponseWriter, r *http.Request) {
	response := jwk.GetJWKs()
	logger.Debugf("Sending JWKs response: %s", response)
	io.WriteString(w, response)
}

func handleCookies(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost && r.Method != http.MethodDelete {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	cookie, err := BuildGetiCookie(r)
	if err != nil {
		logger.Error(err)
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	http.SetCookie(w, &cookie)
}

func registerRoutes() {
	http.HandleFunc("/api/v1/keys/", handleKeys)
	http.HandleFunc("/api/v1/set_cookie", handleCookies)
}

func StartServer(port string) {
	registerRoutes()

	address := ":" + port
	logger.Infof("Starting HTTP server on address %s", address)
	err := http.ListenAndServe(address, logRequestMiddleware(http.DefaultServeMux))
	if err != nil {
		logger.Fatalf("failed to listen: %v", err)
	}
}
