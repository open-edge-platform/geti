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

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { SearchRuleField } from '../../core/media/media-filter.interface';
import { projectRender as render } from '../../test-utils/project-provider-render';
import { MediaFilter } from './media-filter.component';

describe('MediaFilter', () => {
    beforeEach(() => {
        Element.prototype.scrollIntoView = jest.fn();
    });

    it('render MediaFilter', async () => {
        const onSetFilterOptions = jest.fn();

        await render(
            <MediaFilter
                filterOptions={{}}
                onSetFilterOptions={onSetFilterOptions}
                totalMatches={12}
                isMediaFetching={false}
                isMediaFilterEmpty={false}
            />
        );

        expect(onSetFilterOptions).not.toHaveBeenCalled();
    });

    it('correctly disables specific filter rules', async () => {
        const onSetFilterOptions = jest.fn();

        await render(
            <MediaFilter
                filterOptions={{}}
                onSetFilterOptions={onSetFilterOptions}
                disabledFilterRules={[SearchRuleField.UserName]}
                totalMatches={12}
                isMediaFetching={false}
                isMediaFilterEmpty={false}
            />
        );

        await userEvent.click(screen.getByLabelText('Filter media'));
        await userEvent.click(screen.getByText('New filter'));

        await userEvent.click(screen.getAllByLabelText('media-filter-field')[0]);

        // Make sure that the dropdown is showing
        expect(screen.queryByText('Media height')).toBeInTheDocument();

        // The disabled field "SearchRuleField.UserName" should not be shown
        expect(screen.queryByText('Annotation creator')).not.toBeInTheDocument();
    });
});
