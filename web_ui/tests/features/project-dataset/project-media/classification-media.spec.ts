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

import cloneDeep from 'lodash/cloneDeep';
import range from 'lodash/range';

import { paths } from '../../../../src/core/services/routes';
import { MEDIA_CONTENT_BUCKET } from '../../../../src/providers/media-upload-provider/media-upload.interface';
import { test } from '../../../fixtures/base-test';
import { resolveAntelopePath } from '../../../utils/dataset';
import { project } from './../../../mocks/classification/classification.mock';

const classificationLabels = [
    {
        id: '64a51adbc7bf707395ca7e69',
        name: 'Clubs',
        is_anomalous: false,
        color: '#00f5d4ff',
        hotkey: '',
        is_empty: false,
        group: 'Classification labels',
        parent_id: null,
    },
    {
        id: '64a51adbc7bf707395ca7e6a',
        name: '7',
        is_anomalous: false,
        color: '#26518eff',
        hotkey: '',
        is_empty: false,
        group: 'Classification labels',
        parent_id: null,
    },
];
test('Upload media with label', async ({ page, mediaPage, registerApiResponse }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => {
        const classificationProject = cloneDeep(project);
        classificationProject.pipeline.tasks[1].labels = classificationLabels;
        return res(ctx.json(classificationProject));
    });

    const url = paths.project.dataset.media({
        organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
        workspaceId: '61011e42d891c82e13ec92da',
        projectId: project.id,
        datasetId: project.datasets[0].id,
    });
    await page.goto(url);

    const files = range(1, 4).map((_) => resolveAntelopePath());

    const bucket = await mediaPage.getBucket(MEDIA_CONTENT_BUCKET.GENERIC);
    await bucket.uploadFiles(files, ['7', 'Clubs']);
});
