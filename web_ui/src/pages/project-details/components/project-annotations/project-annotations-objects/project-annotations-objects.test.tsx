// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';

import { providersRender } from '../../../../../test-utils/required-providers-render';
import { ProjectAnnotationsObjects } from './project-annotations-objects.component';
import { reorderObjectsLabels } from './utils';

const mockObjectsPerLabel = (id = '1234', name = 'test-name', color = '#000', value = 1) => ({
    id,
    color,
    name,
    value,
});

describe('Project annotations objects', () => {
    it('should render correctly', async () => {
        providersRender(<ProjectAnnotationsObjects objectsPerLabel={[]} gridArea='objects' />);
        const objectsTitle = screen.getByText('Number of objects per label');
        expect(objectsTitle).toBeInTheDocument();
    });

    it('reorder empty labels', async () => {
        const noObjectLabel = mockObjectsPerLabel('1', 'No object');
        const emptyLabel = mockObjectsPerLabel('2', 'empty');
        const labelsOne = mockObjectsPerLabel('3', 'test-1');
        const labelsTwo = mockObjectsPerLabel('4', 'test-2');

        expect(reorderObjectsLabels([labelsTwo, labelsOne])).toEqual([labelsTwo, labelsOne]);
        expect(reorderObjectsLabels([noObjectLabel, labelsOne])).toEqual([labelsOne, noObjectLabel]);
        expect(reorderObjectsLabels([labelsOne, noObjectLabel, labelsTwo])).toEqual([
            labelsOne,
            labelsTwo,
            noObjectLabel,
        ]);
        expect(reorderObjectsLabels([emptyLabel, labelsOne, noObjectLabel, labelsTwo])).toEqual([
            labelsOne,
            labelsTwo,
            emptyLabel,
            noObjectLabel,
        ]);
    });
});
