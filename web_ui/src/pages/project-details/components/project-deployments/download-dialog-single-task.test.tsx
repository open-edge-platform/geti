// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { createInMemoryCodeDeploymentService } from '../../../../core/code-deployment/services/in-memory-code-deployment-service';
import { ModelsGroups } from '../../../../core/models/models.interface';
import { createInMemoryModelsService } from '../../../../core/models/services/in-memory-models-service';
import { Task } from '../../../../core/projects/task.interface';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import {
    getMockedModelGroups,
    getMockedOptimizedModel,
    getMockedTrainedModel,
} from '../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { CustomRenderOptions, providersRender } from '../../../../test-utils/required-providers-render';
import { DownloadDialogSingleTask } from './download-dialog-single-task.component';
import { DEPLOYMENT_PACKAGE_TYPES } from './select-deployment-package.component';

const render = ({
    close = jest.fn(),
    modelsGroups,
    task,
    options = {
        featureFlags: {
            FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: true,
        },
    },
}: {
    close?: () => void;
    task?: Task;
    modelsGroups?: ModelsGroups[];
    options?: CustomRenderOptions;
} = {}) => {
    const mockedTask = task ?? getMockedTask({ id: '123' });
    const mockedModelsGroups = modelsGroups ?? [getMockedModelGroups({ taskId: mockedTask.id })];

    providersRender(
        <DownloadDialogSingleTask
            close={close}
            task={mockedTask}
            projectIdentifier={getMockedProjectIdentifier()}
            modelsGroups={mockedModelsGroups}
        />,
        options
    );
};

describe('DownloadDialogSingleTask', () => {
    const task = getMockedTask({ id: '123' });
    const modelsGroups = [getMockedModelGroups({ taskId: task.id })];
    const [modelVersion] = modelsGroups[0].modelVersions;
    const optimizedModels = [
        getMockedOptimizedModel({ id: modelVersion.id, version: modelVersion.version, modelStatus: 'SUCCESS' }),
    ];
    const modelsService = createInMemoryModelsService();
    modelsService.getModel = async () => {
        return Promise.resolve({
            trainedModel: getMockedTrainedModel(),
            optimizedModels,
            purgeInfo: {
                isPurged: false,
                purgeTime: '',
                userId: '',
            },
            labels: [],
            trainingDatasetInfo: {
                revisionId: '',
                storageId: '',
            },
        });
    };

    describe('with FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE enabled', () => {
        it('allows user to select deployment package', async () => {
            render({ task, modelsGroups });

            expect(await screen.findByRole('button', { name: 'Download' })).toBeEnabled();

            await userEvent.click(
                screen.getByRole('button', { name: `${DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT} Deployment package` })
            );

            expect(screen.getByRole('option', { name: DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT })).toBeVisible();
            expect(screen.getByRole('option', { name: DEPLOYMENT_PACKAGE_TYPES.OVMS_DEPLOYMENT })).toBeVisible();
        });

        it('selects OVMS package and sends request to download deployment package', async () => {
            const close = jest.fn();
            const codeDeploymentService = createInMemoryCodeDeploymentService();
            codeDeploymentService.downloadDeploymentPackage = jest.fn();

            render({
                task,
                close,
                modelsGroups,
                options: {
                    featureFlags: { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: true },
                    services: { modelsService, codeDeploymentService },
                },
            });

            expect(await screen.findByRole('button', { name: 'Download' })).toBeEnabled();

            await userEvent.click(
                screen.getByRole('button', { name: `${DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT} Deployment package` })
            );
            await userEvent.click(screen.getByRole('option', { name: DEPLOYMENT_PACKAGE_TYPES.OVMS_DEPLOYMENT }));

            await userEvent.click(screen.getByRole('button', { name: 'Download' }));

            await waitFor(() => {
                expect(codeDeploymentService.downloadDeploymentPackage).toHaveBeenCalled();
            });
            expect(close).toHaveBeenCalled();
        });

        it('selects code deployment package and sends request to download code deployment package', async () => {
            const close = jest.fn();

            const codeDeploymentService = createInMemoryCodeDeploymentService();
            codeDeploymentService.downloadDeploymentPackage = jest.fn();

            render({
                task,
                close,
                modelsGroups,
                options: {
                    featureFlags: { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: true },
                    services: { modelsService, codeDeploymentService },
                },
            });

            expect(await screen.findByRole('button', { name: 'Download' })).toBeEnabled();

            await userEvent.click(screen.getByRole('button', { name: 'Download' }));

            await waitFor(() => {
                expect(codeDeploymentService.downloadDeploymentPackage).toHaveBeenCalled();
            });
            expect(close).toHaveBeenCalled();
        });
    });

    describe('with FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE disabled', () => {
        it(`doesn't allow user to select deployment package`, () => {
            render({ options: { featureFlags: { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: false } } });

            expect(
                screen.queryByRole('button', {
                    name: `${DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT} Deployment package`,
                })
            ).not.toBeInTheDocument();
        });

        it('sends request to download code deployment package', async () => {
            const close = jest.fn();

            const codeDeploymentService = createInMemoryCodeDeploymentService();
            codeDeploymentService.downloadDeploymentPackage = jest.fn();

            render({
                task,
                close,
                modelsGroups,
                options: {
                    featureFlags: { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: false },
                    services: { modelsService, codeDeploymentService },
                },
            });

            expect(await screen.findByRole('button', { name: 'Download' })).toBeEnabled();

            await userEvent.click(screen.getByRole('button', { name: 'Download' }));

            await waitFor(() => {
                expect(codeDeploymentService.downloadDeploymentPackage).toHaveBeenCalled();
            });
        });
    });
});
