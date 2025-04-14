// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { getMockedTreeGroup } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { LabelTreeViewGroup } from './label-tree-view-group.component';

describe('LabelTreeViewGroup', () => {
    const item = getMockedTreeGroup({ name: 'Color', id: 'color-group' });

    it('Check if edition mode is properly displayed', async () => {
        render(
            <LabelTreeViewGroup
                item={item}
                savedItem={item}
                newTree={false}
                onOpenClickHandler={jest.fn()}
                flatListProjectItems={[]}
                isOpen={true}
                save={jest.fn()}
                inEditionMode={true}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        expect(screen.getByRole('textbox', { name: 'Label group name' })).toBeInTheDocument();
    });
});
