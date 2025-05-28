// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package main

import (
	"context"
	"image"
	"image/png"

	"geti.com/iai_core/env"
	"geti.com/iai_core/logger"
	"geti.com/iai_core/middleware"
	"geti.com/iai_core/storage/minio"
	"geti.com/iai_core/telemetry"
	"github.com/gin-contrib/pprof"
	"github.com/gin-gonic/gin"
	"golang.org/x/image/bmp"
	"golang.org/x/image/tiff"

	"media/app/controller"
	"media/app/service"
	"media/app/usecase"
)

const (
	fallbackPort    = "5002"
	baseDisplayPath = "/api/v1/organizations/:organization_id/workspaces/:workspace_id/projects/:project_id/datasets/:dataset_id/media/images/:image_id/display"
)

func main() {
	// This initializes the supported image formats with their respective decoders.
	// jpg/jpeg are by default supported in the image package.
	image.RegisterFormat("png", "png", png.Decode, png.DecodeConfig)
	image.RegisterFormat("bmp", "bmp", bmp.Decode, bmp.DecodeConfig)
	image.RegisterFormat("tiff", "tiff", tiff.Decode, tiff.DecodeConfig)
	image.RegisterFormat("tif", "tif", tiff.Decode, tiff.DecodeConfig)

	logger.Initialize()
	cleanup := telemetry.SetupTracing(context.Background())
	defer cleanup()

	router := createRouter()
	port := env.GetEnv("PORT", fallbackPort)
	if err := router.Run(":" + port); err != nil {
		logger.Log().Fatalf("Cannot run server: %s", err)
	}
}

// createRouter initializes and returns a new instance of *gin.Engine.
// This function abstracts the setup of routes/route groups.
func createRouter() *gin.Engine {
	router := gin.New()

	router.Use(gin.Recovery())
	router.Use(middleware.ZapRequestLogger(logger.Log().Desugar()))
	router.Use(middleware.ErrorHandler())
	router.Use(telemetry.Middleware())
	router.Use(middleware.CacheControl())

	if err := router.SetTrustedProxies(nil); err != nil {
		logger.Log().Fatalf("Cannot set trusted proxies: %s", err)
	}

	imageRepo := minio.NewImageRepositoryImpl()
	cropper := service.NewResizeCropper()
	createThumbnailUseCase, err := usecase.NewGetOrCreateImageThumbnail(imageRepo, cropper)
	if err != nil {
		logger.Log().Fatalf("Cannot initiate create thumbnail use case: %s", err)
	}
	imageController := controller.NewImageController(createThumbnailUseCase, imageRepo)

	pprof.Register(router, "media/debug/pprof")
	images := router.Group(baseDisplayPath)
	{
		images.GET("/full", imageController.GetImage)
		images.GET("/thumb", imageController.GetThumbnail)
	}

	return router
}
