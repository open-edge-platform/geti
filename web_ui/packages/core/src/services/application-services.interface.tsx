// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import axios from 'axios';

import { AnnotationService } from '../../../../src/core/annotations/services/annotation-service.interface';
import { InferenceService } from '../../../../src/core/annotations/services/inference-service.interface';
import { VisualPromptService } from '../../../../src/core/annotations/services/visual-prompt-service';
import { AuthService } from '../../../../src/core/auth/services/auth-service.interface';
import { CodeDeploymentService } from '../../../../src/core/code-deployment/services/code-deployment-service.interface';
import { CreateApiModelConfigParametersService } from '../../../../src/core/configurable-parameters/services/api-model-config-parameters-service';
import { ProductsService } from '../../../../src/core/credits/products/services/products-service.interface';
import { CreditsService } from '../../../../src/core/credits/services/credits-service.interface';
import { SubscriptionsService } from '../../../../src/core/credits/subscriptions/services/subscription-service.interface';
import { TransactionsService } from '../../../../src/core/credits/transactions/services/transactions-service.interface';
import { TrainingDatasetService } from '../../../../src/core/datasets/services/api-training-dataset-service';
import { DatasetImportService } from '../../../../src/core/datasets/services/dataset.interface';
import { FeatureFlagService } from '../../../../src/core/feature-flags/services/feature-flag-service.interface';
import { JobsService } from '../../../../src/core/jobs/services/jobs-service.interface';
import { MaintenanceService } from '../../../../src/core/maintenance/services/maintenance.interface';
import { MediaService } from '../../../../src/core/media/services/media-service.interface';
import { ModelsService } from '../../../../src/core/models/services/models.interface';
import { OrganizationsService } from '../../../../src/core/organizations/services/organizations-service.interface';
import { PersonalAccessTokensService } from '../../../../src/core/personal-access-tokens/personal-access-tokens.interface';
import { PlatformUtilsService } from '../../../../src/core/platform-utils/services/utils.interface';
import { ProjectService } from '../../../../src/core/projects/services/project-service.interface';
import { API_URLS } from '../../../../src/core/services/urls';
import { ApiModelStatisticsServiceInterface } from '../../../../src/core/statistics/services/api-model-statistics-service';
import { DatasetStatisticsService } from '../../../../src/core/statistics/services/dataset-statistics.interface';
import { StatusService } from '../../../../src/core/status/services/status-service.interface';
import { SupportedAlgorithmsService } from '../../../../src/core/supported-algorithms/services/supported-algorithms.interface';
import { TestsService } from '../../../../src/core/tests/services/tests-service.interface';
import { UserSettingsService } from '../../../../src/core/user-settings/services/user-settings.interface';
import { OnboardingService } from '../../../../src/core/users/services/onboarding-service.interface';
import { UsersService } from '../../../../src/core/users/services/users-service.interface';
import { WorkspacesService } from '../../../../src/core/workspaces/services/workspaces-service.interface';

export interface ApplicationServices {
    router: typeof API_URLS;
    useInMemoryEnvironment: boolean;
    authService: AuthService;
    mediaService: MediaService;
    datasetStatisticsService: DatasetStatisticsService;
    modelStatisticsService: ApiModelStatisticsServiceInterface;
    testsService: TestsService;
    modelsService: ModelsService;
    projectService: ProjectService;
    personalAccessTokensService: PersonalAccessTokensService;
    annotationService: AnnotationService;
    inferenceService: InferenceService;
    visualPromptService: VisualPromptService;
    featureFlagService: FeatureFlagService;
    datasetImportService: DatasetImportService;
    codeDeploymentService: CodeDeploymentService;
    trainingDatasetService: TrainingDatasetService;
    supportedAlgorithmsService: SupportedAlgorithmsService;
    jobsService: JobsService;
    platformUtilsService: PlatformUtilsService;
    workspacesService: WorkspacesService;
    organizationsService: OrganizationsService;
    usersService: UsersService;
    onboardingService: OnboardingService;
    statusService: StatusService;
    configParametersService: CreateApiModelConfigParametersService;
    creditsService: CreditsService;
    productsService: ProductsService;
    transactionsService: TransactionsService;
    subscriptionsService: SubscriptionsService;
    maintenanceService: MaintenanceService;
    userSettingsService: UserSettingsService;
}

export interface ServiceConfiguration {
    router: typeof API_URLS;
    instance: ReturnType<typeof axios.create>;
}
