// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { DOMAIN } from '../../../core/projects/core.interface';
import { getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { FlatTreeView } from './flat-tree-view.component';

describe('FlatTreeView', () => {
    const actions = {
        save: jest.fn(),
        addChild: jest.fn(),
        deleteItem: jest.fn(),
        reorder: jest.fn(),
    };

    it('Check if new labels are shown on the top', async () => {
        const labels = [
            getMockedTreeLabel({ name: 'Label 1' }),
            getMockedTreeLabel({ name: 'Label 2' }),
            getMockedTreeLabel({ name: 'Label 3' }),
        ];

        render(
            <FlatTreeView
                labels={labels}
                actions={actions}
                isEditable={false}
                domains={[DOMAIN.CLASSIFICATION]}
                projectLabels={labels}
                treeValidationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        const treeItems = screen.getAllByRole('listitem');

        expect(treeItems[0]).toHaveTextContent('Label 1');
        expect(treeItems[1]).toHaveTextContent('Label 2');
        expect(treeItems[2]).toHaveTextContent('Label 3');
    });
});
