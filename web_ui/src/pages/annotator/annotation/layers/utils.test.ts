// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
