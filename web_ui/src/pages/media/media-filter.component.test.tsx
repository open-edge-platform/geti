// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
