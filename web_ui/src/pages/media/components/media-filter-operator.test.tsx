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

import { SearchRuleField, SearchRuleOperator } from '../../../core/media/media-filter.interface';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { MediaFilterOperator } from './media-filter-operator.component';

describe('MediaFilterOperator', () => {
    const onSelectionChange = jest.fn();
    const ariaLabel = 'media-filter-operator';

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('allows to select the options and call onSelectionChange', async () => {
        await render(
            <MediaFilterOperator
                value=''
                isAnomalyProject={false}
                field={SearchRuleField.MediaHeight}
                onSelectionChange={onSelectionChange}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /media-filter-operator/i }));
        fireEvent.click(screen.getByRole('menuitemradio', { hidden: true, name: 'Equal' }));

        expect(onSelectionChange).toHaveBeenCalledWith(SearchRuleOperator.Equal);
    });

    it('selects the first item if it is the only one on the list', async () => {
        // Note: SearchRuleField.MediaType only has one operator ("EQUAL")
        await render(
            <MediaFilterOperator
                value=''
                isAnomalyProject={false}
                field={SearchRuleField.MediaType}
                onSelectionChange={onSelectionChange}
            />
        );

        expect(onSelectionChange).toHaveBeenCalledWith(SearchRuleOperator.Equal);
    });

    it('calls onSelectionChange and disable it when field is LabelId', async () => {
        await render(
            <MediaFilterOperator
                isAnomalyProject={true}
                field={SearchRuleField.LabelId}
                value={SearchRuleOperator.Greater}
                onSelectionChange={onSelectionChange}
            />
        );

        const input = screen.getByLabelText(ariaLabel) as HTMLInputElement;

        expect(input.disabled).toBe(true);
        expect(onSelectionChange).toHaveBeenNthCalledWith(1, SearchRuleOperator.In);
    });

    it('calls onSelectionChange and disable it when field is AnnotationSceneState', async () => {
        await render(
            <MediaFilterOperator
                isAnomalyProject={true}
                field={SearchRuleField.AnnotationSceneState}
                value={SearchRuleOperator.Greater}
                onSelectionChange={onSelectionChange}
            />
        );

        const input = screen.getByLabelText(ariaLabel) as HTMLInputElement;

        expect(input.disabled).toBe(true);
        expect(onSelectionChange).toHaveBeenNthCalledWith(1, SearchRuleOperator.Equal);
    });

    it('do not disable with AnomalyProject when "isDatasetAccordion" is true', async () => {
        await render(
            <MediaFilterOperator
                isAnomalyProject={true}
                isDatasetAccordion={true}
                field={SearchRuleField.AnnotationSceneState}
                value={SearchRuleOperator.Greater}
                onSelectionChange={onSelectionChange}
            />
        );

        const input = screen.getByLabelText(ariaLabel) as HTMLInputElement;

        expect(input.disabled).toBe(false);
    });
});
