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

import { labelFromUser } from '../../../../src/core/annotations/utils';
import { OpenApiFixtures } from '../../../fixtures/open-api';
import { media, project, userAnnotationsResponse } from '../../../mocks/segmentation/mocks';
import { registerFullImage, registerFullVideoFrame } from '../../../utils/api';
import { resolveTestAssetPath } from '../../../utils/dataset';

const labelId = '6101254defba22ca453f11c6';
const annotations = [
    {
        id: '7fc5f2ec-c80f-434f-8f1e-90690e2ae41f',
        shape: { type: 'RECTANGLE', x: 562, y: 391, width: 158, height: 244 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: 'a4b40db3-d1c2-4cbe-90bf-016895f284d1',
        shape: { type: 'RECTANGLE', x: 539, y: 267, width: 181, height: 196 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: 'e6370a06-b7a1-46c6-a4da-e61850823ac6',
        shape: { type: 'RECTANGLE', x: 380, y: 33, width: 199, height: 217 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: '72dade1c-f7be-4e37-8173-a8b16f39e3cc',
        shape: { type: 'RECTANGLE', x: 0, y: 140, width: 196, height: 208 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: '03b7ffc7-2e88-4fbe-b3a4-e4166a9c0fe6',
        shape: { type: 'RECTANGLE', x: 0, y: 441, width: 173, height: 242 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: 'be74e4d0-a331-48c8-ba5e-eed0e904715f',
        shape: { type: 'RECTANGLE', x: 209, y: 205, width: 143, height: 205 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: '95c3e121-3684-47fb-8fd7-91c0639d2833',
        shape: { type: 'RECTANGLE', x: 308, y: 356, width: 198, height: 236 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: '00d823a0-2368-4cda-99ab-a2cdffecc375',
        shape: { type: 'RECTANGLE', x: 197, y: 565, width: 163, height: 223 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: 'ce1f1b88-fdf1-42e6-83a8-7b62364a5157',
        shape: { type: 'RECTANGLE', x: 99, y: 750, width: 231, height: 171 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
    {
        id: '74279a1f-1c63-421d-8721-abf339c5dc7f',
        shape: { type: 'RECTANGLE', x: 428, y: 638, width: 222, height: 263 },
        labels: [{ id: labelId, probability: 1 }],
        labels_to_revisit: [],
    },
];

export const activeModelPredictions = annotations.filter((_, idx) => idx < 3);
export const visualPromptPredictions = annotations;

export const registerProjectResponses = (registerApiResponse: OpenApiFixtures['registerApiResponse']) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
    registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
    registerFullImage(registerApiResponse, resolveTestAssetPath('multiple-cards.webp'));
    registerFullVideoFrame(registerApiResponse, resolveTestAssetPath('multiple-cards.webp'));
    registerApiResponse('CreateImageAnnotation', (req, res, ctx) => {
        const annotationsWithUserId = req.body.annotations.map((annotation) => {
            return {
                ...annotation,
                // @ts-expect-error the type of annotation from the request is incorrect
                labels: annotation.labels.map((label) => labelFromUser(label)),
            };
        });
        return res(
            ctx.json({
                ...req.body,
                annotations: annotationsWithUserId,
            })
        );
    });

    registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
        return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
    });
    registerApiResponse('GetVideoFrameAnnotation', (_, res, ctx) => {
        return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
    });
};
