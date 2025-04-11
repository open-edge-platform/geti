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

import { test as baseTest, expect } from '@playwright/test';

import { extendWithOpenApi } from './open-api';
import { AILearningConfigurationPage } from './page-objects/ai-learning-configuration-page';
import { AnomalyProjectMediaPage } from './page-objects/anomaly-project-media-page';
import { CameraPage } from './page-objects/camera-page';
import { ConfigurationParametersPage } from './page-objects/configuration-parameters-page';
import { CreateProjectPage } from './page-objects/create-project-page';
import { DatasetStatisticsPage } from './page-objects/dataset-statistics-page';
import { ImportProjectDatasetPage } from './page-objects/import-project-dataset.page';
import { IntelAdminPage } from './page-objects/intel-admin-page';
import { LabelsPage } from './page-objects/labels-page';
import { LoginPage } from './page-objects/login-page';
import { MembersPage } from './page-objects/members-page';
import { ModelMetricsPage } from './page-objects/model-metrics-page';
import { ProjectModelsPage } from './page-objects/models-page';
import { OnboardingPage } from './page-objects/onboarding-page';
import { PersonalAccessTokenPage } from './page-objects/personal-access-token-page';
import { ProjectDatasetPage } from './page-objects/project-dataset-page';
import { ProjectMediaPage } from './page-objects/project-media-page';
import { ProjectPage } from './page-objects/project-page';
import { ProjectUsersPage } from './page-objects/project-users-page';
import { QuickInferencePage } from './page-objects/quick-inference-page';
import { TemplateManagerPage } from './page-objects/template-manager';
import { ProjectTestPage } from './page-objects/test-page';
import { ProjectTestsPage } from './page-objects/tests-page';
import { WorkspacesPage } from './page-objects/workspaces-page';

interface BaseFixtures {
    loginPage: LoginPage;
    workspacesPage: WorkspacesPage;
    modelsPage: ProjectModelsPage;
    projectPage: ProjectPage;
    createProjectPage: CreateProjectPage;
    testsPage: ProjectTestsPage;
    testPage: ProjectTestPage;
    quickInferencePage: QuickInferencePage;
    labelsPage: LabelsPage;
    importProjectDatasetPage: ImportProjectDatasetPage;
    datasetPage: ProjectDatasetPage;
    mediaPage: ProjectMediaPage;
    cameraPage: CameraPage;
    anomalyMediaPage: AnomalyProjectMediaPage;
    projectUsersPage: ProjectUsersPage;
    configurationParametersPage: ConfigurationParametersPage;
    aiLearningConfigurationPage: AILearningConfigurationPage;
    onboardingPage: OnboardingPage;
    personalAccessTokenPage: PersonalAccessTokenPage;
    membersPage: MembersPage;
    templateManagerPage: TemplateManagerPage;
    intelAdminPage: IntelAdminPage;
    modelMetricsPage: ModelMetricsPage;
    datasetStatisticsPage: DatasetStatisticsPage;
}

const test = extendWithOpenApi(baseTest).extend<BaseFixtures>({
    loginPage: async ({ page }, use) => {
        await use(new LoginPage(page));
    },
    workspacesPage: async ({ page }, use) => {
        await use(new WorkspacesPage(page));
    },
    projectPage: async ({ page }, use) => {
        await use(new ProjectPage(page));
    },
    createProjectPage: async ({ page }, use) => {
        await use(new CreateProjectPage(page));
    },
    testsPage: async ({ page }, use) => {
        await use(new ProjectTestsPage(page));
    },
    testPage: async ({ page }, use) => {
        await use(new ProjectTestPage(page));
    },
    quickInferencePage: async ({ page }, use) => {
        await use(new QuickInferencePage(page));
    },
    modelsPage: async ({ page }, use) => {
        await use(new ProjectModelsPage(page));
    },
    labelsPage: async ({ page }, use) => {
        await use(new LabelsPage(page));
    },
    datasetPage: async ({ page }, use) => {
        await use(new ProjectDatasetPage(page));
    },
    mediaPage: async ({ page }, use) => {
        await use(new ProjectMediaPage(page));
    },
    anomalyMediaPage: async ({ page, mediaPage }, use) => {
        await use(new AnomalyProjectMediaPage(page, mediaPage));
    },
    projectUsersPage: async ({ page }, use) => {
        await use(new ProjectUsersPage(page));
    },
    configurationParametersPage: async ({ page }, use) => {
        await use(new ConfigurationParametersPage(page));
    },
    aiLearningConfigurationPage: async ({ page }, use) => {
        await use(new AILearningConfigurationPage(page));
    },
    onboardingPage: async ({ page }, use) => {
        await use(new OnboardingPage(page));
    },
    cameraPage: async ({ page }, use) => {
        await use(new CameraPage(page));
    },
    importProjectDatasetPage: async ({ page }, use) => {
        await use(new ImportProjectDatasetPage(page));
    },
    personalAccessTokenPage: async ({ page }, use) => {
        await use(new PersonalAccessTokenPage(page));
    },
    membersPage: async ({ page }, use) => {
        await use(new MembersPage(page));
    },
    templateManagerPage: async ({ page }, use) => {
        await use(new TemplateManagerPage(page));
    },
    intelAdminPage: async ({ page }, use) => {
        await use(new IntelAdminPage(page));
    },
    modelMetricsPage: async ({ page }, use) => {
        await use(new ModelMetricsPage(page));
    },
    datasetStatisticsPage: async ({ page }, use) => {
        await use(new DatasetStatisticsPage(page));
    },
});

export { expect, test };
