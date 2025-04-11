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

import { labelFromUser } from '../../../../core/annotations/utils';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedExplanation } from '../../../../test-utils/mocked-items-factory/mocked-explanation';
import { labels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { filterByExplanationSelection, isExplanationSelected } from './utils';

const [labelOne, labelTwo, labelThree] = labels;

const mockedExplanationLabelOne = getMockedExplanation({
    id: '123',
    labelsId: labelOne.id,
});
const mockedExplanationLabelThree = getMockedExplanation({
    id: '432',
    labelsId: labelThree.id,
});

describe('annotation layers utils', () => {
    it('isExplanationSelected', () => {
        expect(isExplanationSelected(true, undefined)).toBe(false);
        expect(isExplanationSelected(false, undefined)).toBe(false);

        expect(isExplanationSelected(true, mockedExplanationLabelOne)).toBe(true);
        expect(isExplanationSelected(false, mockedExplanationLabelOne)).toBe(false);
    });
});

describe('filterByExplanationSelection', () => {
    const annotationLabelOne = getMockedAnnotation({ labels: [labelFromUser(labelOne)] });
    const annotationLabelTwo = getMockedAnnotation({ labels: [labelFromUser(labelTwo)] });
    const annotationClassification = getMockedAnnotation({
        labels: [labelFromUser(labelOne), labelFromUser(labelTwo)],
    });

    it('match selected explanation label', () => {
        expect(filterByExplanationSelection([annotationLabelOne], false, mockedExplanationLabelOne)).toEqual([
            annotationLabelOne,
        ]);
    });

    it('does not match selected explanation label', () => {
        expect(filterByExplanationSelection([annotationLabelTwo], false, mockedExplanationLabelOne)).toEqual([]);
    });

    it('classification annotation has selected explanation label', () => {
        expect(filterByExplanationSelection([annotationClassification], true, mockedExplanationLabelOne)).toEqual([
            { ...annotationClassification, labels: [annotationClassification.labels[0]] },
        ]);
    });

    it('classification annotation does not have matched selected explanation label', () => {
        expect(filterByExplanationSelection([annotationClassification], true, mockedExplanationLabelThree)).toEqual([]);
    });
});
