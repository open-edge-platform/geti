// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createInMemoryAnnotationService } from '../annotations/services/in-memory-annotation-service';
import { createInMemoryInferenceService } from '../annotations/services/in-memory-inference-service';
import { createInMemoryVisualPromptService } from '../annotations/services/inference-service/in-memory-visual-prompt-service';
import { createInMemoryAuthService } from '../auth/services/in-memory-auth-service';
import { createInMemoryCodeDeploymentService } from '../code-deployment/services/in-memory-code-deployment-service';
import { createInMemoryApiModelConfigParametersService } from '../configurable-parameters/services/in-memory-api-model-config-parameters-service';
import { createInMemoryProductsService } from '../credits/products/services/in-memory-products-service';
import { createInMemoryCreditsService } from '../credits/services/in-memory-credits-service';
import { createInMemorySubscriptionsService } from '../credits/subscriptions/services/in-memory-subscription-service';
import { createInMemoryTransactionsService } from '../credits/transactions/services/in-memory-transactions-service';
import { createInMemoryDatasetImportService } from '../datasets/services/in-memory-dataset-import-service';
import { createInMemoryTrainingDatasetService } from '../datasets/services/in-memory-training-dataset-service';
import { createInMemoryApiFeatureFlagService } from '../feature-flags/services/in-memory-api-feature-flag-service';
import { createInMemoryJobsService } from '../jobs/services/in-memory-jobs-service';
import { createInMemoryApiMaintenanceService } from '../maintenance/services/in-memory-api-maintenance-service';
import { createInMemoryMediaService } from '../media/services/in-memory-media-service/in-memory-media-service';
import { createInMemoryModelsService } from '../models/services/in-memory-models-service';
import { createInMemoryOrganizationsService } from '../organizations/services/in-memory-organizations-service';
import { createInMemoryPersonalAccessTokensService } from '../personal-access-tokens/in-memory-personal-access-tokens-service';
import { createInMemoryPlatformUtilsService } from '../platform-utils/services/create-in-memory-platform-utils-service';
import { createInMemoryProjectService } from '../projects/services/in-memory-project-service';
import { createInMemoryDatasetStatisticsService } from '../statistics/services/in-memory-api-dataset-statistics-service';
import { createInMemoryModelStatisticsService } from '../statistics/services/in-memory-api-model-statistics-service';
import { createInMemoryStatusService } from '../status/services/in-memory-status-service';
import { createInMemorySupportedAlgorithmsService } from '../supported-algorithms/services/in-memory-supported-algorithms-service';
import { createInMemoryTestsService } from '../tests/services/in-memory-tests-service';
import { createInMemoryUserSettingsService } from '../user-settings/services/in-memory-user-settings-service';
import { createInMemoryUsersService } from '../users/services/in-memory-users-service';
import { createInMemoryOnboardingService } from '../users/services/inmemory-onboarding-service';
import { createInMemoryApiWorkspacesService } from '../workspaces/services/in-memory-api-workspaces-service';
import { ApplicationServices, ServiceConfiguration } from './application-services.interface';

export const getInMemoryServices = (serviceConfiguration: ServiceConfiguration): ApplicationServices => {
    return {
        router: serviceConfiguration.router,
        useInMemoryEnvironment: true,
        authService: createInMemoryAuthService(),
        codeDeploymentService: createInMemoryCodeDeploymentService(),
        testsService: createInMemoryTestsService(),
        mediaService: createInMemoryMediaService(),
        datasetStatisticsService: createInMemoryDatasetStatisticsService(),
        modelStatisticsService: createInMemoryModelStatisticsService(),
        projectService: createInMemoryProjectService(),
        personalAccessTokensService: createInMemoryPersonalAccessTokensService(),
        annotationService: createInMemoryAnnotationService(),
        inferenceService: createInMemoryInferenceService(),
        visualPromptService: createInMemoryVisualPromptService(),
        datasetImportService: createInMemoryDatasetImportService(),
        modelsService: createInMemoryModelsService(),
        trainingDatasetService: createInMemoryTrainingDatasetService(),
        featureFlagService: createInMemoryApiFeatureFlagService(),
        supportedAlgorithmsService: createInMemorySupportedAlgorithmsService(),
        jobsService: createInMemoryJobsService(),
        platformUtilsService: createInMemoryPlatformUtilsService(),
        workspacesService: createInMemoryApiWorkspacesService(),
        organizationsService: createInMemoryOrganizationsService(),
        usersService: createInMemoryUsersService(),
        onboardingService: createInMemoryOnboardingService(),
        statusService: createInMemoryStatusService(),
        configParametersService: createInMemoryApiModelConfigParametersService(),
        creditsService: createInMemoryCreditsService(),
        productsService: createInMemoryProductsService(),
        transactionsService: createInMemoryTransactionsService(),
        subscriptionsService: createInMemorySubscriptionsService(),
        maintenanceService: createInMemoryApiMaintenanceService(),
        userSettingsService: createInMemoryUserSettingsService(),
    };
};
