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

import { expect } from '@playwright/test';
import range from 'lodash/range';
import { v4 as uuidV4 } from 'uuid';

import { MAX_SUPPORTED_ANNOTATIONS } from '../../../../src/core/annotations/utils';
import { TUTORIAL_CARD_KEYS } from '../../../../src/core/user-settings/dtos/user-settings.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { settings } from '../../../fixtures/open-api/mocks';
import { switchCallsAfter } from '../../../utils/api';
import { annotatorUrl, userAnnotationsResponse } from './../../../mocks/segmentation/mocks';

// FIXME: At the moment we can't set the prediction limit which means that when
// this test is run we use the default limit (100k) which makes this test fail
// due to it being too slow
test.fixme('Limit predictions shown to a user', async ({ registerApiResponse, page, annotationListPage }) => {
    registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
        res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
    );

    registerApiResponse('GetSinglePrediction', (_, res, ctx) => {
        const count = MAX_SUPPORTED_ANNOTATIONS + 10;

        return res(
            ctx.json({
                predictions: range(0, count).map((index) => {
                    // Put the annotations in a neat grid
                    const shape = {
                        type: 'RECTANGLE',
                        x: (index % 80) * 10 + 10,
                        y: (Math.floor(index / 80) % 60) * 10 + 10,
                        width: 5,
                        height: 5,
                    } as const;

                    const labels = [
                        {
                            color: '#0015ffff',
                            id: '6101254defba22ca453f11c6',
                            name: 'horse',
                            probability: 0.1,
                            source: {
                                model_id: 'some-model',
                                model_storage_id: 'some-model-storage',
                                user_id: null,
                            },
                        },
                    ];

                    return {
                        id: uuidV4(),
                        labels,
                        labels_to_revisit: [],
                        modified: 'today',
                        shape,
                    };
                }),
            })
        );
    });

    // The first two requests for get settings mock the user and project settings,
    // after this we mock the settings after the user dismissed the tutorial card
    const switchAfterSavingSettings = switchCallsAfter(2);
    // Since we're dealing with a lot of annotations, we optimize this test by hiding labels
    const settingsWithoutLabels = { ...JSON.parse(settings), hideLabels: { defaultValue: false, value: true } };
    registerApiResponse(
        'GetSettings',
        switchAfterSavingSettings([
            async (_, res, ctx) => {
                return res(ctx.status(200), ctx.json({ settings: JSON.stringify(settingsWithoutLabels) }));
            },
            async (_, res, ctx) => {
                return res(
                    ctx.status(200),
                    ctx.json({
                        settings: JSON.stringify({
                            ...settingsWithoutLabels,
                            [TUTORIAL_CARD_KEYS.ANNOTATIONS_COUNT_LIMIT]: {
                                isEnabled: false,
                            },
                        }),
                    })
                );
            },
        ])
    );

    await page.goto(annotatorUrl);

    await annotationListPage.expectTotalAnnotationsToBe(MAX_SUPPORTED_ANNOTATIONS);

    const dismissButton = page.getByRole('button', { name: 'Dismiss' });
    await dismissButton.click();

    await expect(dismissButton).toBeHidden();

    // Check that the tools are disabled
    await expect(page.getByRole('button', { name: 'Bounding Box' })).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Detection assistant' })).toBeDisabled();
});
