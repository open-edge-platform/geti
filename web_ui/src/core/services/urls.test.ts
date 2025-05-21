// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedProjectIdentifier } from '../../test-utils/mocked-items-factory/mocked-identifiers';
import { PredictionCache, PredictionMode } from '../annotations/services/prediction-service.interface';
import { MEDIA_TYPE } from '../media/base-media.interface';
import { MediaIdentifier } from '../media/media.interface';
import { SortDirection } from '../shared/query-parameters';
import { API_URLS, MEDIA_ITEM } from './urls';

describe('urls', () => {
    const projectIdentifier = getMockedProjectIdentifier();
    const comaEncoded = `%2C`;

    it('JOBS_QUERY_PARAMS', () => {
        const workspaceIdentifier = { workspaceId: 'workspaceId-test', organizationId: 'organizationId-test' };

        expect(API_URLS.JOBS_QUERY_PARAMS(workspaceIdentifier, {})).toContain('/jobs?sort_by=creation_time');
        expect(API_URLS.JOBS_QUERY_PARAMS(workspaceIdentifier, { sortDirection: SortDirection.ASC })).toContain(
            '/jobs?sort_by=creation_time&sort_direction=asc'
        );
        expect(API_URLS.JOBS_QUERY_PARAMS(workspaceIdentifier, { sortDirection: SortDirection.DESC })).toContain(
            '/jobs?sort_by=creation_time&sort_direction=desc'
        );
    });

    it('EXPLAIN_NEW', () => {
        const taskId = '123321';
        const rect = { x: 10, y: 20, height: 50, width: 100 };

        expect(API_URLS.EXPLAIN_NEW(projectIdentifier)).toContain('/active:explain');
        expect(API_URLS.EXPLAIN_NEW(projectIdentifier, undefined, rect)).toContain(
            `/active:explain?roi=10${comaEncoded}20${comaEncoded}100${comaEncoded}50`
        );
        expect(API_URLS.EXPLAIN_NEW(projectIdentifier, taskId, rect)).toContain(
            `/${taskId}:explain?roi=10${comaEncoded}20${comaEncoded}100${comaEncoded}50`
        );
    });

    it('PREDICTION_NEW', () => {
        const taskId = '123321';
        const rect = { x: 0, y: 0, height: 10, width: 20 };

        expect(API_URLS.PREDICTION_NEW(projectIdentifier)).toContain('/active:predict?use_cache=auto');
        expect(API_URLS.PREDICTION_NEW(projectIdentifier, PredictionCache.NEVER)).toContain(
            '/active:predict?use_cache=never'
        );

        expect(API_URLS.PREDICTION_NEW(projectIdentifier, PredictionCache.NEVER, undefined, rect)).toContain(
            `/active:predict?use_cache=never&roi=0${comaEncoded}0${comaEncoded}20${comaEncoded}10`
        );

        expect(API_URLS.PREDICTION_NEW(projectIdentifier, PredictionCache.NEVER, taskId, rect)).toContain(
            `/${taskId}:predict?use_cache=never&roi=0${comaEncoded}0${comaEncoded}20${comaEncoded}10`
        );
    });

    it('PREDICTION', () => {
        const organizationId = 'organization-id';
        const workspaceId = 'test-workspaceId';
        const projectId = 'test-projectId';
        const datasetId = 'test-datasetId';
        const datasetIdentifier = {
            datasetId,
            organizationId,
            projectId,
            workspaceId,
        };
        const mediaIdentifier: MediaIdentifier = {
            type: MEDIA_TYPE.IMAGE,
            imageId: 'imageId',
        };
        const taskId = 'test-taskId';
        const mode = PredictionMode.AUTO;
        const selectedInputId = 'test-selectedInputId';
        const root = MEDIA_ITEM(datasetIdentifier, mediaIdentifier);

        expect(API_URLS.PREDICTION(datasetIdentifier, mediaIdentifier, mode, taskId, selectedInputId)).toEqual(
            `${root}/predictions/${mode}?task_id=${taskId}&roi_id=${selectedInputId}`
        );

        expect(API_URLS.PREDICTION(datasetIdentifier, mediaIdentifier, mode, taskId)).toEqual(
            `${root}/predictions/${mode}?task_id=${taskId}`
        );

        expect(API_URLS.PREDICTION(datasetIdentifier, mediaIdentifier, mode)).toEqual(`${root}/predictions/${mode}?`);

        expect(API_URLS.PREDICTION(datasetIdentifier, mediaIdentifier, mode, undefined, selectedInputId)).toEqual(
            `${root}/predictions/${mode}?roi_id=${selectedInputId}`
        );
    });
});
