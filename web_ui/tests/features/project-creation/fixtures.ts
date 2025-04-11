// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { v4 } from 'uuid';

import type { ProjectDTO } from '../../../src/core/projects/dtos/project.interface';
import { test as baseTest } from '../../fixtures/base-test';
import { CreateProjectPage } from '../../fixtures/page-objects/create-project-page';

interface CreateProjectFixtures {
    createProject: CreateProjectPage;
}

const test = baseTest.extend<CreateProjectFixtures>({
    createProjectPage: async ({ page, workspacesPage, createProjectPage }, use) => {
        await page.goto('/', { timeout: 15000 });
        await workspacesPage.createProject();

        await use(createProjectPage);
    },
});

// OpenAPI integration
const ANOMALY_LABELS = [
    {
        color: '#8bae46ff',
        group: 'default - Anomaly classification',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f8',
        is_anomalous: false,
        is_empty: false,
        name: 'Normal',
        parent_id: null,
    },
    {
        color: '#ff5662ff',
        group: 'default - Anomaly classification',
        hotkey: '',
        id: '63283aedc80c9c686fd3b1f6',
        is_anomalous: true,
        is_empty: false,
        name: 'Anomalous',
        parent_id: null,
    },
];

export const testWithOpenApi = test.extend<CreateProjectFixtures>({
    createProjectPage: async ({ createProjectPage, registerApiResponse, openApi }, use) => {
        // Mock createProject nad GetProjectInfo so that whenever the user creates a project,
        // we will return that project on the subsequent GetProjectInfo request
        let project: undefined | ProjectDTO = undefined;
        registerApiResponse('CreateProject', (req, res, ctx) => {
            const { mock, status } = openApi.mockResponseForOperation('CreateProject');

            const { name, pipeline } = req.body;
            const tasks = pipeline.tasks.map((task) => {
                // In case of an anomaly project the server is supposed to generate the labels
                if (task.task_type.includes('anomaly')) {
                    return { ...task, id: v4(), labels: ANOMALY_LABELS };
                }

                // The UI does not fill the id, hotkey, is_empty and is_anomalous fields,
                // thus we provide them with default values
                const labels = (task.labels ?? []).map((label) => {
                    return {
                        ...label,
                        id: label.name,
                        hotkey: label.hotkey ?? '',
                        is_empty: false,
                        is_anomalous: false,
                    };
                });

                return { ...task, id: v4(), labels };
            });
            project = { ...mock, name, pipeline: { connections: req.body.pipeline.connections, tasks } };

            return res(ctx.json(mock), ctx.status(status));
        });

        registerApiResponse('GetProjectInfo', (_, res, ctx) => {
            const { mock, status } = openApi.mockResponseForOperation('GetProjectInfo');

            return res(ctx.status(status), ctx.json(project ?? mock));
        });

        use(createProjectPage);
    },
});
