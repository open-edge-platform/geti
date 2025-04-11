// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package utils

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

const (
	loggingConfigDirEnvVarName = "LOGGING_CONFIG_DIR"
	logLevelFilename           = "LOG_LEVEL"
	loggerSyncerSleepTime      = 30 * time.Second
)

var currentLogger *zap.SugaredLogger
var loggerInitializationMutex sync.Mutex

func syncLogLevel(loggerLevel *zap.AtomicLevel) {
	logLevelMapping := map[string]zapcore.Level{
		"debug":   zapcore.DebugLevel,
		"info":    zapcore.InfoLevel,
		"warning": zapcore.WarnLevel,
		"error":   zapcore.ErrorLevel,
	}
	for {
		loggingConfigDir := os.Getenv(loggingConfigDirEnvVarName)
		levelFilePath := filepath.Join(loggingConfigDir, logLevelFilename)
		logLevelFromFileBytes, err := os.ReadFile(levelFilePath)
		if err != nil {
			fmt.Printf("logger syncer exited due to error reading level file: %v\n", levelFilePath)
			return
		}
		logLevelFromFile := string(logLevelFromFileBytes[:])
		requestedLogLevelLowered := strings.ToLower(logLevelFromFile)

		zapLevelConverted := logLevelMapping[requestedLogLevelLowered]

		loggerLevel.SetLevel(zapLevelConverted)
		time.Sleep(loggerSyncerSleepTime)
	}
}

func InitializeLogger() *zap.SugaredLogger {
	loggerInitializationMutex.Lock()
	defer loggerInitializationMutex.Unlock()
	if currentLogger != nil {
		return currentLogger
	}
	encoderConfig := zap.NewProductionEncoderConfig()
	encoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	encoderConfig.EncodeCaller = callerEncoder
	encoderConfig.EncodeLevel = levelEncoder
	encoder := zapcore.NewConsoleEncoder(encoderConfig)
	mutexedStdoutWriteSyncer := zapcore.Lock(os.Stdout)
	atomicLevel := zap.NewAtomicLevel()
	coreLogger := zapcore.NewCore(encoder, mutexedStdoutWriteSyncer, atomicLevel)
	zapLogger := zap.New(coreLogger, zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))
	sugaredLogger := zapLogger.Sugar()

	go syncLogLevel(&atomicLevel)

	currentLogger = sugaredLogger

	return sugaredLogger
}

func callerEncoder(caller zapcore.EntryCaller, enc zapcore.PrimitiveArrayEncoder) {
	enc.AppendString("[" + caller.TrimmedPath() + "]:")
}

func levelEncoder(level zapcore.Level, enc zapcore.PrimitiveArrayEncoder) {
	enc.AppendString(fmt.Sprintf("[%-8s]", level.CapitalString()))
}
