// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromUser } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { defaultToolForProject, getInitialAnnotations } from './utils';

const mockedLabel = labelFromUser(getMockedLabel({ name: 'label-1', id: 'label-1' }));
const mockedAnnotation = getMockedAnnotation({ labels: [mockedLabel] }, ShapeType.Rect);
const mockedInvalidAnnotation = getMockedAnnotation({ id: 'invalid-annotation', labels: [] }, ShapeType.Rect);
const mockedPrediction = getMockedAnnotation({ id: 'prediction', labels: [mockedLabel] }, ShapeType.Rect);

describe('default annotator tool', () => {
    it('selects the polygon tool when annotating a segmentation project', () => {
        expect(defaultToolForProject([DOMAIN.SEGMENTATION, DOMAIN.CLASSIFICATION])).toBe(ToolType.PolygonTool);
    });

    it('selects the detection tool when annotating a segmentation project', () => {
        expect(defaultToolForProject([DOMAIN.DETECTION])).toBe(ToolType.BoxTool);
    });

    it('selects the selection tool when annotating a segmentation project', () => {
        expect(defaultToolForProject([DOMAIN.CLASSIFICATION])).toBe(ToolType.SelectTool);
    });
});

describe('getInitialAnnotations', () => {
    it('getInitialAnnotations', () => {
        expect(getInitialAnnotations([])).toEqual([]);
        expect(getInitialAnnotations(undefined, [])).toEqual([]);

        expect(getInitialAnnotations([], [mockedPrediction])).toEqual([mockedPrediction]);
        expect(getInitialAnnotations([mockedInvalidAnnotation], [mockedPrediction])).toEqual([mockedPrediction]);

        expect(getInitialAnnotations([mockedAnnotation], [])).toEqual([mockedAnnotation]);
        expect(getInitialAnnotations([mockedAnnotation], [mockedPrediction])).toEqual([mockedAnnotation]);
    });

    it('returns annotations without lables if there are no predictions', () => {
        const annotations = [getMockedAnnotation({ labels: [] }, ShapeType.Rect)];

        expect(getInitialAnnotations(annotations, [])).toEqual(annotations);
    });
});
