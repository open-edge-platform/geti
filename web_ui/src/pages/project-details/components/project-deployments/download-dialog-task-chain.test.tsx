// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
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
import { DownloadDialogTaskChain } from './download-dialog-task-chain.component';
import { DEPLOYMENT_PACKAGE_TYPES } from './select-deployment-package.component';

const render = ({
    close = jest.fn(),
    modelsGroups,
    tasks,
    options = {
        featureFlags: {
            FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: true,
        },
    },
}: {
    close?: () => void;
    tasks?: Task[];
    modelsGroups?: ModelsGroups[];
    options?: CustomRenderOptions;
} = {}) => {
    const mockedTask = tasks ?? [getMockedTask({ id: '123' }), getMockedTask({ id: '321' })];
    const mockedModelsGroups = modelsGroups ?? [
        getMockedModelGroups({ taskId: mockedTask[0].id }),
        getMockedModelGroups({ taskId: mockedTask[1].id }),
    ];

    return providersRender(
        <DownloadDialogTaskChain
            close={close}
            modelsGroups={mockedModelsGroups}
            tasks={mockedTask}
            projectIdentifier={getMockedProjectIdentifier()}
        />,
        options
    );
};

describe('DownloadDialogTaskChain', () => {
    const tasks = [getMockedTask({ id: '123' }), getMockedTask({ id: '321' })];
    const modelsGroups = [
        getMockedModelGroups({ taskId: tasks[0].id, groupId: 'group-id-123' }),
        getMockedModelGroups({ taskId: tasks[1].id, groupId: 'group-id-321' }),
    ];
    const [modelVersionForFirstTask] = modelsGroups[0].modelVersions;
    const [modelVersionForSecondTask] = modelsGroups[1].modelVersions;

    const optimizedModelsForFirstTask = [
        getMockedOptimizedModel({
            id: modelVersionForFirstTask.id,
            version: modelVersionForFirstTask.version,
            modelStatus: 'SUCCESS',
        }),
    ];
    const optimizedModelsForSecondTask = [
        getMockedOptimizedModel({
            id: modelVersionForSecondTask.id,
            version: modelVersionForSecondTask.version,
            modelStatus: 'SUCCESS',
        }),
    ];
    const modelsService = createInMemoryModelsService();
    modelsService.getModel = async (params) => {
        return Promise.resolve({
            trainedModel: getMockedTrainedModel(),
            optimizedModels:
                params.groupId === modelsGroups[0].groupId ? optimizedModelsForFirstTask : optimizedModelsForSecondTask,
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
        it('allows user to select deployment package only in the first task', async () => {
            render();

            expect(await screen.findByRole('button', { name: 'Next' })).toBeEnabled();

            await userEvent.click(
                screen.getByRole('button', { name: `${DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT} Deployment package` })
            );

            expect(screen.getByRole('option', { name: DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT })).toBeVisible();
            expect(screen.getByRole('option', { name: DEPLOYMENT_PACKAGE_TYPES.OVMS_DEPLOYMENT })).toBeVisible();

            await userEvent.click(screen.getByRole('option', { name: DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT }));
            await userEvent.click(screen.getByRole('button', { name: 'Next' }));

            expect(
                screen.getByRole('button', { name: `${DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT} Deployment package` })
            ).toBeDisabled();
        });

        it('sends request to download OVMS deployment package', async () => {
            const close = jest.fn();

            const codeDeploymentService = createInMemoryCodeDeploymentService();
            codeDeploymentService.downloadDeploymentPackage = jest.fn();

            render({
                tasks,
                close,
                modelsGroups,
                options: {
                    featureFlags: { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: true },
                    services: { modelsService, codeDeploymentService },
                },
            });

            expect(await screen.findByRole('button', { name: 'Next' })).toBeEnabled();

            await userEvent.click(
                screen.getByRole('button', { name: `${DEPLOYMENT_PACKAGE_TYPES.CODE_DEPLOYMENT} Deployment package` })
            );

            await userEvent.click(screen.getByRole('option', { name: DEPLOYMENT_PACKAGE_TYPES.OVMS_DEPLOYMENT }));

            expect(await screen.findByRole('button', { name: 'Next' })).toBeEnabled();

            await userEvent.click(screen.getByRole('button', { name: 'Next' }));
            await userEvent.click(screen.getByRole('button', { name: 'Download' }));

            await waitFor(() => {
                expect(codeDeploymentService.downloadDeploymentPackage).toHaveBeenCalled();
            });

            expect(close).toHaveBeenCalled();
        });

        it('sends request to download code deployment package', async () => {
            const close = jest.fn();

            const codeDeploymentService = createInMemoryCodeDeploymentService();
            codeDeploymentService.downloadDeploymentPackage = jest.fn();

            render({
                tasks,
                close,
                modelsGroups,
                options: {
                    featureFlags: { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: true },
                    services: { modelsService, codeDeploymentService },
                },
            });

            expect(await screen.findByRole('button', { name: 'Next' })).toBeEnabled();

            await userEvent.click(screen.getByRole('button', { name: 'Next' }));
            await userEvent.click(screen.getByRole('button', { name: 'Download' }));

            await waitFor(() => {
                expect(codeDeploymentService.downloadDeploymentPackage).toHaveBeenCalled();
            });

            expect(close).toHaveBeenCalled();
        });
    });

    describe('with FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE disabled', () => {
        it(`doesn't allow user to select deployment package`, async () => {
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
                tasks,
                close,
                modelsGroups,
                options: {
                    featureFlags: { FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: false },
                    services: { modelsService, codeDeploymentService },
                },
            });

            expect(await screen.findByRole('button', { name: 'Next' })).toBeEnabled();

            await userEvent.click(screen.getByRole('button', { name: 'Next' }));
            await userEvent.click(screen.getByRole('button', { name: 'Download' }));

            await waitFor(() => {
                expect(codeDeploymentService.downloadDeploymentPackage).toHaveBeenCalled();
            });
            expect(close).toHaveBeenCalled();
        });
    });
});
