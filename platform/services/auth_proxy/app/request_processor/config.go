// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package request_processor

import (
	"auth_proxy/app/utils"
	"fmt"
	"go.uber.org/zap"
	"os"
	"strings"
	"time"
)

const (
	envUnauthorizedURLs string = "UNAUTHORIZED_URLS"
	envJwtTtlGeti       string = "JWT_TTL_GETI"
	envCacheTtl         string = "CACHE_TTL_SECONDS"
	envCacheSizeMB      string = "CACHE_SIZE_MB"
)

type AuthProxyConfiguration struct {
	IssInternal   string
	AudInternal   string
	IssExternal   string
	AudExternal   string
	RequiredRoles []string
}

func LoadAuthProxyConfiguration() (*AuthProxyConfiguration, error) {
	config := &AuthProxyConfiguration{
		IssInternal:   os.Getenv("ISS_INTERNAL"),
		AudInternal:   os.Getenv("AUD_INTERNAL"),
		IssExternal:   os.Getenv("ISS_EXTERNAL"),
		AudExternal:   os.Getenv("AUD_EXTERNAL"),
		RequiredRoles: strings.Split(os.Getenv("REQUIRED_ROLES"), ","),
	}

	checkedFields := []string{config.IssExternal, config.AudInternal, config.IssExternal, config.AudExternal}
	allSet := true
	noneSet := true
	for _, field := range checkedFields {
		if field != "" {
			noneSet = false
		} else {
			allSet = false
		}
	}

	if allSet {
		return config, nil
	} else if noneSet {
		return nil, nil
	} else {
		return nil, fmt.Errorf("auth proxy configuration - not all required fields are fully set: %v", config)
	}
}

func GetJwtTtlGeti() (time.Duration, error) {
	return utils.GetEnvAsDuration(envJwtTtlGeti, "60m")
}

func GetCacheTtl() (int, error) {
	return utils.GetEnvAsInt(envCacheTtl, "60")
}

func GetCacheSizeMB() (int, error) {
	return utils.GetEnvAsInt(envCacheSizeMB, "10")
}

func GetUnauthorizedURLs() []string {
	var unauthorizedURLs []string
	unauthorizedURLsFromEnv := utils.GetEnv(envUnauthorizedURLs, "/api/v1/profile,/api/v1/logout,/api/v1/onboarding/user,/api/v1/feature_flags")

	unauthorizedURLsSplitted := strings.Split(unauthorizedURLsFromEnv, ",")

	for _, path := range unauthorizedURLsSplitted {
		urlTrimmed := strings.TrimSpace(path)
		unauthorizedURLs = append(unauthorizedURLs, urlTrimmed)
	}
	return unauthorizedURLs
}

type RequestProcessingLogger struct {
	Handler     *RequestHandler
	basicLogger *zap.SugaredLogger
}

func InitializeRequestProcessingLogger(handler *RequestHandler) *RequestProcessingLogger {
	return &RequestProcessingLogger{
		Handler:     handler,
		basicLogger: utils.InitializeBasicLogger(),
	}
}

func (rpl *RequestProcessingLogger) logWithCaller(level string, format string, args ...interface{}) {
	// Format the log message to include the request ID and path
	logMessage := fmt.Sprintf("Req ID %s, path %s. %s", rpl.Handler.RequestID, rpl.Handler.RequestPath, fmt.Sprintf(format, args...))

	// Create a new logger with the overridden caller information
	loggerWithCaller := rpl.basicLogger.WithOptions(zap.AddCallerSkip(2))

	switch level {
	case "info":
		loggerWithCaller.Infow(logMessage)
	case "error":
		loggerWithCaller.Errorw(logMessage)
	case "debug":
		loggerWithCaller.Debugw(logMessage)
	case "warn":
		loggerWithCaller.Warnw(logMessage)
	default:
		loggerWithCaller.Infow(logMessage)
	}
}

func (rpl *RequestProcessingLogger) Infof(format string, args ...interface{}) {
	rpl.logWithCaller("info", format, args...)
}

func (rpl *RequestProcessingLogger) Errorf(format string, args ...interface{}) {
	rpl.logWithCaller("error", format, args...)
}

func (rpl *RequestProcessingLogger) Debugf(format string, args ...interface{}) {
	rpl.logWithCaller("debug", format, args...)
}

func (rpl *RequestProcessingLogger) Warnf(format string, args ...interface{}) {
	rpl.logWithCaller("warn", format, args...)
}
