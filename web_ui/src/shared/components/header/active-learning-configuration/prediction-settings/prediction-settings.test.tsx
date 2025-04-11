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

import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { createInMemoryUserSettingsService } from '../../../../../core/user-settings/services/in-memory-user-settings-service';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedUserProjectSettings } from '../../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { PredictionsSettings } from './predictions-settings.component';

const getSuggestPredictions = () => {
    return screen.getByRole('switch', { name: 'Suggest predictions' });
};

const getModelType = () => {
    return screen.queryByText('Model type');
};

const getActiveLearningModel = () => {
    return screen.getByRole('radio', {
        name: /active learning model/i,
    });
};

const getPromptModel = () => {
    return screen.getByRole('radio', {
        name: /prompt model/i,
    });
};

describe('PredictionSettings', () => {
    it('toggling suggest prediction updates user settings initial prediction key', async () => {
        const userProjectSettings = getMockedUserProjectSettings();
        userProjectSettings.initialPredictionAsAnnotations.isEnabled = true;

        const userSettingsService = createInMemoryUserSettingsService();
        userSettingsService.getProjectSettings = async () => {
            return userProjectSettings;
        };
        userSettingsService.saveProjectSettings = jest.fn(() => {
            userProjectSettings.initialPredictionAsAnnotations.isEnabled = false;
            return Promise.resolve();
        });

        await render(<PredictionsSettings />, {
            services: {
                userSettingsService,
            },
        });

        expect(getSuggestPredictions()).toBeChecked();
        await userEvent.click(getSuggestPredictions());

        await waitFor(() => {
            expect(getSuggestPredictions()).not.toBeChecked();
        });

        expect(userSettingsService.saveProjectSettings).toHaveBeenCalledWith(expect.anything(), {
            ...userProjectSettings,
            initialPredictionAsAnnotations: {
                ...userProjectSettings.initialPredictionAsAnnotations,
                isEnabled: false,
            },
        });
    });

    it('does not display model type when FEATURE_FLAG_VISUAL_PROMPT_SERVICE is not enabled', async () => {
        await render(<PredictionsSettings />, { featureFlags: { FEATURE_FLAG_VISUAL_PROMPT_SERVICE: false } });

        expect(getModelType()).not.toBeInTheDocument();
    });

    it('does not display model type for classification', async () => {
        const project = getMockedProject({
            tasks: [getMockedTask({ id: '1', domain: DOMAIN.CLASSIFICATION })],
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => Promise.resolve(project);

        await render(<PredictionsSettings />, {
            services: {
                projectService,
            },
        });

        expect(getModelType()).not.toBeInTheDocument();
    });

    it('does not display model type for anomaly', async () => {
        const project = getMockedProject({
            tasks: [getMockedTask({ id: '1', domain: DOMAIN.ANOMALY_CLASSIFICATION })],
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => Promise.resolve(project);

        await render(<PredictionsSettings />, {
            services: {
                projectService,
            },
        });

        expect(getModelType()).not.toBeInTheDocument();
    });

    it('does not display model type for task chain', async () => {
        const project = getMockedProject({
            tasks: [
                getMockedTask({ id: '1', domain: DOMAIN.DETECTION }),
                getMockedTask({ id: '2', domain: DOMAIN.CLASSIFICATION }),
            ],
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => Promise.resolve(project);

        await render(<PredictionsSettings />, {
            services: {
                projectService,
            },
        });

        expect(getModelType()).not.toBeInTheDocument();
    });

    it('selecting model type updates user settings inference model', async () => {
        const project = getMockedProject({
            tasks: [getMockedTask({ id: '1', domain: DOMAIN.DETECTION })],
        });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => Promise.resolve(project);

        const userProjectSettings = getMockedUserProjectSettings();
        userProjectSettings.inferenceModel.isEnabled = true;

        const userSettingsService = createInMemoryUserSettingsService();
        userSettingsService.getProjectSettings = async () => {
            return userProjectSettings;
        };
        userSettingsService.saveProjectSettings = jest.fn(() => {
            userProjectSettings.inferenceModel.isEnabled = false;
            return Promise.resolve();
        });

        await render(<PredictionsSettings />, {
            services: {
                userSettingsService,
                projectService,
            },
            featureFlags: {
                FEATURE_FLAG_VISUAL_PROMPT_SERVICE: true,
            },
        });

        expect(getModelType()).toBeInTheDocument();
        expect(getActiveLearningModel()).toBeChecked();

        await userEvent.click(getPromptModel());

        await waitFor(() => {
            expect(getPromptModel()).toBeChecked();
        });

        expect(userSettingsService.saveProjectSettings).toHaveBeenCalledWith(expect.anything(), {
            ...userProjectSettings,
            inferenceModel: {
                ...userProjectSettings.inferenceModel,
                isEnabled: false,
            },
        });
    });
});
