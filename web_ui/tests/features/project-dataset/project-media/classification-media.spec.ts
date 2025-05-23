// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { cloneDeep, range } from 'lodash-es';

import { paths } from '@geti/core/src/services/routes';
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
