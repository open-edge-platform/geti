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

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { CopyPersonalAccessToken } from './copy-personal-access-token.component';

describe('CopyKey', () => {
    it('renders component', () => {
        render(<CopyPersonalAccessToken personalAccessToken={'apiKey-test'} personalAccessTokenId='' />);
        const button = screen.getByLabelText('copy-api-key');

        expect(button).toBeInTheDocument();
    });
});
