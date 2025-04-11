// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import axios from 'axios';

import { AnnotationService } from '../annotations/services/annotation-service.interface';
import { InferenceService } from '../annotations/services/inference-service.interface';
import { VisualPromptService } from '../annotations/services/visual-prompt-service';
import { AuthService } from '../auth/services/auth-service.interface';
import { CodeDeploymentService } from '../code-deployment/services/code-deployment-service.interface';
import { CreateApiModelConfigParametersService } from '../configurable-parameters/services/api-model-config-parameters-service';
import { ProductsService } from '../credits/products/services/products-service.interface';
import { CreditsService } from '../credits/services/credits-service.interface';
import { SubscriptionsService } from '../credits/subscriptions/services/subscription-service.interface';
import { TransactionsService } from '../credits/transactions/services/transactions-service.interface';
import { TrainingDatasetService } from '../datasets/services/api-training-dataset-service';
import { DatasetImportService } from '../datasets/services/dataset.interface';
import { FeatureFlagService } from '../feature-flags/services/feature-flag-service.interface';
import { JobsService } from '../jobs/services/jobs-service.interface';
import { MaintenanceService } from '../maintenance/services/maintenance.interface';
import { MediaService } from '../media/services/media-service.interface';
import { ModelsService } from '../models/services/models.interface';
import { OrganizationsService } from '../organizations/services/organizations-service.interface';
import { PersonalAccessTokensService } from '../personal-access-tokens/personal-access-tokens.interface';
import { PlatformUtilsService } from '../platform-utils/services/utils.interface';
import { ProjectService } from '../projects/services/project-service.interface';
import { ApiModelStatisticsServiceInterface } from '../statistics/services/api-model-statistics-service';
import { DatasetStatisticsService } from '../statistics/services/dataset-statistics.interface';
import { StatusService } from '../status/services/status-service.interface';
import { SupportedAlgorithmsService } from '../supported-algorithms/services/supported-algorithms.interface';
import { TestsService } from '../tests/services/tests-service.interface';
import { UserSettingsService } from '../user-settings/services/user-settings.interface';
import { OnboardingService } from '../users/services/onboarding-service.interface';
import { UsersService } from '../users/services/users-service.interface';
import { WorkspacesService } from '../workspaces/services/workspaces-service.interface';
import { API_URLS } from './urls';

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
