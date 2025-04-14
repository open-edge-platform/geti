// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { SearchRuleField } from '../../../core/media/media-filter.interface';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { FIELD_OPTIONS } from '../utils';
import { MediaFilterField } from './media-filter-field.component';

describe('MediaFilterField', () => {
    const onSelectionChange = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('allows to select the Label and call onSelectionChange', async () => {
        render(<MediaFilterField value='' onSelectionChange={onSelectionChange} fieldsOptions={FIELD_OPTIONS} />);

        fireEvent.click(screen.getByRole('button', { name: /media-filter-field/i }));
        fireEvent.click(screen.getByRole('menuitemradio', { hidden: true, name: 'Label' }));

        expect(onSelectionChange).toHaveBeenCalledWith(SearchRuleField.LabelId);
    });
});
