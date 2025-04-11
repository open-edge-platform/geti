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

import { fireEvent, screen } from '@testing-library/react';

import { LabelsRelationType } from '../../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../../core/projects/core.interface';
import {
    getMockedTreeGroup,
    getMockedTreeLabel,
} from '../../../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../../../test-utils/required-providers-render';
import { getById } from '../../../../../../test-utils/utils';
import { LABEL_TREE_TYPE } from '../../label-tree-type.enum';
import { LabelTreeLabel } from './label-tree-label.component';

describe('NewLabelTreeLabel', () => {
    const domains = [DOMAIN.DETECTION];

    it('should change color after adding a label', async () => {
        const { container } = render(
            <LabelTreeLabel
                type={LABEL_TREE_TYPE.HIERARCHY}
                projectLabels={[]}
                taskMetadata={{
                    labels: [],
                    relation: LabelsRelationType.SINGLE_SELECTION,
                    domain: DOMAIN.DETECTION,
                }}
                addLabel={jest.fn()}
                name={''}
                color={'#ed3300ff'}
                domains={domains}
                withLabel
            />
        );

        const input = screen.getByLabelText('Label');
        const colorButton = getById(container, 'change-color-button')?.firstElementChild;
        const firstStyling = JSON.stringify(colorButton?.getAttribute('style'));

        fireEvent.change(input, { target: { value: 'Test label' } });
        fireEvent.click(screen.getByRole('button', { name: 'Create label' }));

        const secondStyling = JSON.stringify(colorButton?.getAttribute('style'));
        expect(firstStyling).not.toBe(secondStyling);
    });

    it('Change color - it should not add a label', async () => {
        const addLabelHandler = jest.fn();
        render(
            <LabelTreeLabel
                type={LABEL_TREE_TYPE.FLAT}
                projectLabels={[]}
                taskMetadata={{
                    labels: [],
                    relation: LabelsRelationType.SINGLE_SELECTION,
                    domain: DOMAIN.DETECTION,
                }}
                addLabel={addLabelHandler}
                name={''}
                domains={domains}
                color={'#ed3300ff'}
            />
        );

        const colorButton = screen.getByRole('button', { name: 'Color picker button' });

        fireEvent.click(colorButton);
        fireEvent.click(screen.getByRole('slider', { name: /color/i }));

        expect(addLabelHandler).not.toHaveBeenCalled();
    });

    it('Should disable the "add label" button if the input is empty', async () => {
        render(
            <LabelTreeLabel
                type={LABEL_TREE_TYPE.FLAT}
                projectLabels={[]}
                taskMetadata={{
                    labels: [],
                    relation: LabelsRelationType.SINGLE_SELECTION,
                    domain: DOMAIN.DETECTION,
                }}
                addLabel={jest.fn()}
                name={''}
                domains={domains}
                color={'#ed3300ff'}
            />
        );

        const input = screen.getByLabelText('Project label name input');

        fireEvent.change(input, { target: { value: 'Test label' } });
        expect(screen.getByTestId('add-label-button')).toBeEnabled();

        fireEvent.change(input, { target: { value: '' } });
        expect(screen.getByTestId('add-label-button')).toBeDisabled();
    });

    it('Should be able to add label with the same name like group name', async () => {
        const name = 'animals';
        const labels = [getMockedTreeLabel({ name: 'humans' }), getMockedTreeGroup({ name })];

        render(
            <LabelTreeLabel
                type={LABEL_TREE_TYPE.FLAT}
                projectLabels={labels}
                taskMetadata={{
                    labels: [],
                    relation: LabelsRelationType.SINGLE_SELECTION,
                    domain: DOMAIN.DETECTION,
                }}
                addLabel={jest.fn()}
                name={''}
                domains={domains}
                color={'#ed3300ff'}
            />
        );

        const input = screen.getByLabelText('Project label name input');

        fireEvent.change(input, { target: { value: name } });

        expect(screen.queryByTestId('label-error-message-id')).not.toBeInTheDocument();
        expect(screen.getByTestId('add-label-button')).toBeEnabled();
    });

    it('Should not be able to add label with the same name like existing label name', async () => {
        const name = 'humans';
        const labels = [getMockedTreeLabel({ name }), getMockedTreeGroup({ name: 'animals' })];

        render(
            <LabelTreeLabel
                type={LABEL_TREE_TYPE.FLAT}
                projectLabels={labels}
                taskMetadata={{
                    labels: [],
                    relation: LabelsRelationType.SINGLE_SELECTION,
                    domain: DOMAIN.DETECTION,
                }}
                addLabel={jest.fn()}
                name={''}
                domains={domains}
                color={'#ed3300ff'}
            />
        );

        const input = screen.getByLabelText('Project label name input');

        fireEvent.change(input, { target: { value: name } });

        expect(screen.getByTestId('label-error-message-id')).toBeInTheDocument();
        expect(screen.getByTestId('add-label-button')).toBeDisabled();
    });
});
