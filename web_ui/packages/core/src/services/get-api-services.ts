// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createApiAnnotationService } from '../../../../src/core/annotations/services/api-annotation-service';
import { createApiInferenceService } from '../../../../src/core/annotations/services/inference-service/api-inference-service';
import { createApiVisualPromptService } from '../../../../src/core/annotations/services/inference-service/api-visual-prompt-service';
import { createApiAuthService } from '../../../../src/core/auth/services/api-auth-service';
import { createApiCodeDeploymentService } from '../../../../src/core/code-deployment/services/api-code-deployment-service';
import { createApiModelConfigParametersService } from '../../../../src/core/configurable-parameters/services/api-model-config-parameters-service';
import { createApiProductsService } from '../../../../src/core/credits/products/services/api-products-service';
import { createApiCreditsService } from '../../../../src/core/credits/services/api-credits-service';
import { createApiSubscriptionsService } from '../../../../src/core/credits/subscriptions/services/api-subscriptions-service';
import { createApiTransactionsService } from '../../../../src/core/credits/transactions/services/api-transactions-service';
import { createApiDatasetImportService } from '../../../../src/core/datasets/services/api-dataset-import-service';
import { createApiTrainingDatasetService } from '../../../../src/core/datasets/services/api-training-dataset-service';
import { createApiFeatureFlagService } from '../../../../src/core/feature-flags/services/api-feature-flag-service';
import { createApiJobsService } from '../../../../src/core/jobs/services/api-jobs-service';
import { createApiMaintenanceService } from '../../../../src/core/maintenance/services/api-maintenance-service';
import { createApiMediaService } from '../../../../src/core/media/services/api-media-service/api-media-service';
import { createApiModelsService } from '../../../../src/core/models/services/api-models-service';
import { createApiOrganizationsService } from '../../../../src/core/organizations/services/api-organizations-service';
import { createApiPersonalAccessTokensService } from '../../../../src/core/personal-access-tokens/personal-access-tokens-service';
import { createApiPlatformUtilsService } from '../../../../src/core/platform-utils/services/create-api-platform-utils-service';
import { createApiProjectService } from '../../../../src/core/projects/services/api-project-service';
import { createApiDatasetStatisticsService } from '../../../../src/core/statistics/services/api-dataset-statistics-service';
import { createApiModelStatisticsService } from '../../../../src/core/statistics/services/api-model-statistics-service';
import { createApiStatusService } from '../../../../src/core/status/services/api-status-service';
import { createApiSupportedAlgorithmsService } from '../../../../src/core/supported-algorithms/services/api-supported-algorithms-service';
import { createApiTestsService } from '../../../../src/core/tests/services/api-tests-service';
import { createApiUserSettingsService } from '../../../../src/core/user-settings/services/api-user-settings-service';
import { createApiOnboardingService } from '../../../../src/core/users/services/api-onboarding-service';
import { createApiUsersService } from '../../../../src/core/users/services/api-users-service';
import { createApiWorkspacesService } from '../../../../src/core/workspaces/services/api-workspaces-service';
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
