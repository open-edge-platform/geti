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
