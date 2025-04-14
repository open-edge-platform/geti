// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import keyBy from 'lodash/keyBy';

import { labels as labelMocks } from './../../test-utils/mocked-items-factory/mocked-labels';
import { recursivelyAddLabel, recursivelyRemoveLabels } from './label-resolver';
import { Label } from './label.interface';

describe('labelling annotations', () => {
    const labels = keyBy(labelMocks, (label) => label.id);

    describe('Adding labels', () => {
        const addLabel = (label: Label, annotationLabels: Label[]) => {
            return recursivelyAddLabel(annotationLabels, label, Object.values(labels));
        };

        it('allows us to add a label to an annotation', (): void => {
            expect(addLabel(labels['red'], [])).toEqual([labels['card'], labels['red']]);
        });

        it('adds missing parent labels', (): void => {
            expect(addLabel(labels['♥'], [])).toEqual([labels['card'], labels['red'], labels['♥']]);
        });

        it('removes conflicting labels', (): void => {
            expect(addLabel(labels['♥'], [labels['card'], labels['black'], labels['♠'], labels['4']])).toEqual([
                labels['card'],
                labels['4'],
                labels['red'],
                labels['♥'],
            ]);
        });
    });

    describe('Removing labels', () => {
        const removeLabel = (label: Label, annotationLabels: Label[]) => {
            return recursivelyRemoveLabels(annotationLabels, [label]);
        };

        it('allows us to remove a label from an annotation', (): void => {
            expect(removeLabel(labels['card'], [labels['card']])).toEqual([]);
        });

        it('removes child labels if their parent was removed', (): void => {
            expect(removeLabel(labels['red'], [labels['card'], labels['4'], labels['red'], labels['♥']])).toEqual([
                labels['card'],
                labels['4'],
            ]);
        });
    });
});
