// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
