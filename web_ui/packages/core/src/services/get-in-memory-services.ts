// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createInMemoryAnnotationService } from '../../../../src/core/annotations/services/in-memory-annotation-service';
import { createInMemoryInferenceService } from '../../../../src/core/annotations/services/in-memory-inference-service';
import { createInMemoryVisualPromptService } from '../../../../src/core/annotations/services/inference-service/in-memory-visual-prompt-service';
import { createInMemoryAuthService } from '../../../../src/core/auth/services/in-memory-auth-service';
import { createInMemoryCodeDeploymentService } from '../../../../src/core/code-deployment/services/in-memory-code-deployment-service';
import { createInMemoryApiModelConfigParametersService } from '../../../../src/core/configurable-parameters/services/in-memory-api-model-config-parameters-service';
import { createInMemoryProductsService } from '../../../../src/core/credits/products/services/in-memory-products-service';
import { createInMemoryCreditsService } from '../../../../src/core/credits/services/in-memory-credits-service';
import { createInMemorySubscriptionsService } from '../../../../src/core/credits/subscriptions/services/in-memory-subscription-service';
import { createInMemoryTransactionsService } from '../../../../src/core/credits/transactions/services/in-memory-transactions-service';
import { createInMemoryDatasetImportService } from '../../../../src/core/datasets/services/in-memory-dataset-import-service';
import { createInMemoryTrainingDatasetService } from '../../../../src/core/datasets/services/in-memory-training-dataset-service';
import { createInMemoryApiFeatureFlagService } from '../../../../src/core/feature-flags/services/in-memory-api-feature-flag-service';
import { createInMemoryJobsService } from '../../../../src/core/jobs/services/in-memory-jobs-service';
import { createInMemoryApiMaintenanceService } from '../../../../src/core/maintenance/services/in-memory-api-maintenance-service';
import { createInMemoryMediaService } from '../../../../src/core/media/services/in-memory-media-service/in-memory-media-service';
import { createInMemoryModelsService } from '../../../../src/core/models/services/in-memory-models-service';
import { createInMemoryOrganizationsService } from '../../../../src/core/organizations/services/in-memory-organizations-service';
import { createInMemoryPersonalAccessTokensService } from '../../../../src/core/personal-access-tokens/in-memory-personal-access-tokens-service';
import { createInMemoryPlatformUtilsService } from '../../../../src/core/platform-utils/services/create-in-memory-platform-utils-service';
import { createInMemoryProjectService } from '../../../../src/core/projects/services/in-memory-project-service';
import { createInMemoryDatasetStatisticsService } from '../../../../src/core/statistics/services/in-memory-api-dataset-statistics-service';
import { createInMemoryModelStatisticsService } from '../../../../src/core/statistics/services/in-memory-api-model-statistics-service';
import { createInMemoryStatusService } from '../../../../src/core/status/services/in-memory-status-service';
import { createInMemorySupportedAlgorithmsService } from '../../../../src/core/supported-algorithms/services/in-memory-supported-algorithms-service';
import { createInMemoryTestsService } from '../../../../src/core/tests/services/in-memory-tests-service';
import { createInMemoryUserSettingsService } from '../../../../src/core/user-settings/services/in-memory-user-settings-service';
import { createInMemoryUsersService } from '../../../../src/core/users/services/in-memory-users-service';
import { createInMemoryOnboardingService } from '../../../../src/core/users/services/inmemory-onboarding-service';
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
