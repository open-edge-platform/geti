// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { projectRender } from '../../../../../test-utils/project-provider-render';
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
        projectRender(<ProjectAnnotationsObjects objectsPerLabel={[]} gridArea='objects' />);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

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
