// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

package main

import (
	"context"
	"image"
	"image/png"

	"geti.com/go_sdk/env"
	"geti.com/go_sdk/logger"
	"geti.com/go_sdk/middleware"
	"geti.com/go_sdk/storage/minio"
	"geti.com/go_sdk/telemetry"
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
	router.Use(middleware.ErrorHandler())
	router.Use(telemetry.Middleware())
	router.Use(middleware.CacheControl())

	if err := router.SetTrustedProxies(nil); err != nil {
		logger.Log().Fatalf("Cannot set trusted proxies: %s", err)
	}

	imageRepo := minio.NewImageRepositoryImpl()
	cropper := service.NewResizeCropper()
	createThumbnailUseCase := usecase.NewGetOrCreateImageThumbnail(imageRepo, cropper)
	imageController := controller.NewImageController(createThumbnailUseCase, imageRepo)

	pprof.Register(router, "media/debug/pprof")
	images := router.Group(baseDisplayPath)
	{
		images.GET("/full", imageController.GetImage)
		images.GET("/thumb", imageController.GetThumbnail)
	}

	return router
}
