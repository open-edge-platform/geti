// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createApiAnnotationService } from '../annotations/services/api-annotation-service';
import { createApiInferenceService } from '../annotations/services/inference-service/api-inference-service';
import { createApiVisualPromptService } from '../annotations/services/inference-service/api-visual-prompt-service';
import { createApiAuthService } from '../auth/services/api-auth-service';
import { createApiCodeDeploymentService } from '../code-deployment/services/api-code-deployment-service';
import { createApiModelConfigParametersService } from '../configurable-parameters/services/api-model-config-parameters-service';
import { createApiProductsService } from '../credits/products/services/api-products-service';
import { createApiCreditsService } from '../credits/services/api-credits-service';
import { createApiSubscriptionsService } from '../credits/subscriptions/services/api-subscriptions-service';
import { createApiTransactionsService } from '../credits/transactions/services/api-transactions-service';
import { createApiDatasetImportService } from '../datasets/services/api-dataset-import-service';
import { createApiTrainingDatasetService } from '../datasets/services/api-training-dataset-service';
import { createApiFeatureFlagService } from '../feature-flags/services/api-feature-flag-service';
import { createApiJobsService } from '../jobs/services/api-jobs-service';
import { createApiMaintenanceService } from '../maintenance/services/api-maintenance-service';
import { createApiMediaService } from '../media/services/api-media-service/api-media-service';
import { createApiModelsService } from '../models/services/api-models-service';
import { createApiOrganizationsService } from '../organizations/services/api-organizations-service';
import { createApiPersonalAccessTokensService } from '../personal-access-tokens/personal-access-tokens-service';
import { createApiPlatformUtilsService } from '../platform-utils/services/create-api-platform-utils-service';
import { createApiProjectService } from '../projects/services/api-project-service';
import { createApiDatasetStatisticsService } from '../statistics/services/api-dataset-statistics-service';
import { createApiModelStatisticsService } from '../statistics/services/api-model-statistics-service';
import { createApiStatusService } from '../status/services/api-status-service';
import { createApiSupportedAlgorithmsService } from '../supported-algorithms/services/api-supported-algorithms-service';
import { createApiTestsService } from '../tests/services/api-tests-service';
import { createApiUserSettingsService } from '../user-settings/services/api-user-settings-service';
import { createApiOnboardingService } from '../users/services/api-onboarding-service';
import { createApiUsersService } from '../users/services/api-users-service';
import { createApiWorkspacesService } from '../workspaces/services/api-workspaces-service';
import { ApplicationServices, ServiceConfiguration } from './application-services.interface';

export const getApiServices = (serviceConfiguration: ServiceConfiguration): ApplicationServices => {
    return {
        router: serviceConfiguration.router,
        useInMemoryEnvironment: false,
        authService: createApiAuthService(serviceConfiguration),
        codeDeploymentService: createApiCodeDeploymentService(serviceConfiguration),
        testsService: createApiTestsService(serviceConfiguration),
        mediaService: createApiMediaService(serviceConfiguration),
        datasetStatisticsService: createApiDatasetStatisticsService(serviceConfiguration),
        modelStatisticsService: createApiModelStatisticsService(serviceConfiguration),
        projectService: createApiProjectService(serviceConfiguration),
        personalAccessTokensService: createApiPersonalAccessTokensService(serviceConfiguration),
        annotationService: createApiAnnotationService(serviceConfiguration),
        inferenceService: createApiInferenceService(serviceConfiguration),
        visualPromptService: createApiVisualPromptService(serviceConfiguration),
        datasetImportService: createApiDatasetImportService(serviceConfiguration),
        modelsService: createApiModelsService(serviceConfiguration),
        trainingDatasetService: createApiTrainingDatasetService(serviceConfiguration),
        featureFlagService: createApiFeatureFlagService(serviceConfiguration),
        supportedAlgorithmsService: createApiSupportedAlgorithmsService(serviceConfiguration),
        jobsService: createApiJobsService(serviceConfiguration),
        platformUtilsService: createApiPlatformUtilsService(serviceConfiguration),
        workspacesService: createApiWorkspacesService(serviceConfiguration),
        organizationsService: createApiOrganizationsService(serviceConfiguration),
        usersService: createApiUsersService(serviceConfiguration),
        onboardingService: createApiOnboardingService(serviceConfiguration),
        statusService: createApiStatusService(serviceConfiguration),
        configParametersService: createApiModelConfigParametersService(serviceConfiguration),
        creditsService: createApiCreditsService(serviceConfiguration),
        productsService: createApiProductsService(serviceConfiguration),
        transactionsService: createApiTransactionsService(serviceConfiguration),
        subscriptionsService: createApiSubscriptionsService(serviceConfiguration),
        maintenanceService: createApiMaintenanceService(serviceConfiguration),
        userSettingsService: createApiUserSettingsService(serviceConfiguration),
    };
};
