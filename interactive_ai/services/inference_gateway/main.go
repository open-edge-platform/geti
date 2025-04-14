// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

package main

import (
	"context"

	"geti.com/go_sdk/frames"
	"geti.com/go_sdk/logger"
	"geti.com/go_sdk/middleware"
	"geti.com/go_sdk/storage/minio"
	"geti.com/go_sdk/telemetry"
	"github.com/caarlos0/env/v11"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	"github.com/go-playground/validator/v10"
	"github.com/go-resty/resty/v2"

	"inference_gateway/app/controllers"
	"inference_gateway/app/grpc"
	"inference_gateway/app/service"
	"inference_gateway/app/usecase"
)

type config struct {
	InferenceGatewayPort string `env:"INFERENCE_GATEWAY_PORT" envDefault:"7000"`
	MaxMultipartMemoryMB int64  `env:"MAX_MULTIPART_MEMORY_MB" envDefault:"64"`
}

const (
	baseProjectPath = "/api/v1/organizations/:organization_id/workspaces/:workspace_id/projects/:project_id"
)

func main() {
	logger.Initialize()
	cleanup := telemetry.SetupTracing(context.Background())
	defer cleanup()

	meshClient, err := grpc.NewModelMeshClient()
	if err != nil {
		logger.Log().Fatalf("Cannot run server: %s", err)
	}
	defer func() {
		_ = meshClient.Close()
	}()

	registrationClient, err := grpc.NewModelMeshRegistrationClient()
	if err != nil {
		logger.Log().Fatalf("Cannot run server: %s", err)
	}
	defer func() {
		_ = registrationClient.Close()
	}()

	var cfg config
	if err = env.Parse(&cfg); err != nil {
		logger.Log().Fatalf("Cannot parse environment variables: %s", err)
	}

	modelAccessSrv := service.NewModelAccessService(meshClient, registrationClient)
	router := createRouter(cfg.MaxMultipartMemoryMB, modelAccessSrv)
	if err := router.Run(":" + cfg.InferenceGatewayPort); err != nil {
		logger.Log().Fatalf("Cannot run server: %s", err)
	}
}

// createRouter initializes and returns a new instance of *gin.Engine.
// This function abstracts the setup of routes/route groups.
func createRouter(maxMultipartLimit int64, modelAccessSrv service.ModelAccessService) *gin.Engine {
	r := gin.New()
	r.MaxMultipartMemory = maxMultipartLimit << 20

	r.Use(gin.Recovery())
	r.Use(middleware.ErrorHandler())
	r.Use(telemetry.Middleware())

	if err := r.SetTrustedProxies(nil); err != nil {
		logger.Log().Fatalf("Failed to set trusted proxies %s", err)
	}

	if v, ok := binding.Validator.Engine().(*validator.Validate); ok {
		if err := v.RegisterValidation("activeOr24Hex", controllers.ValidateModelID); err != nil {
			logger.Log().Fatalf("Cannot configure validation: %s", err)
		}
	}

	cacheSrv, err := service.NewPredictionCacheService(resty.New())
	if err != nil {
		logger.Log().Fatalf("Cannot instantiate cache service: %s", err)
	}
	videoRepo := minio.NewVideoRepositoryImpl()
	imageRepo := minio.NewImageRepositoryImpl()
	frameReader := new(frames.FramerReaderImpl)
	frameExtractor := new(frames.FFmpegCLIFrameExtractor)
	mediaSrv := service.NewMediaServiceImpl(videoRepo, imageRepo, frameReader)
	predict := usecase.NewPredict(modelAccessSrv, videoRepo, frameExtractor)
	explain := usecase.NewExplain(modelAccessSrv, videoRepo, frameExtractor)
	requestHandler := controllers.NewRequestHandlerImpl(mediaSrv)

	inferenceCtrl := controllers.NewInferenceControllerImpl(modelAccessSrv, cacheSrv, requestHandler, predict, explain)
	pipelineCtrl := controllers.NewPipelineController(inferenceCtrl)
	// Pipeline endpoints
	pipelines := r.Group(baseProjectPath + "/pipelines/:pipeline_id")
	{
		pipelines.GET("/status", pipelineCtrl.Status)
		pipelines.POST("", pipelineCtrl.Infer)
	}

	// Model endpoints --- Temporarily disabled for SaaS MVP
	//models := r.Group(baseProjectPath + "/models/:model_id")
	//{
	//	models.GET("/status", statusController.Model)
	//	models.POST("", endpoints.ModelEndpoint)
	//}

	return r
}
