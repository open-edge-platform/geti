// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { SecurityPage } from './security-page.component';

describe('security page', () => {
    it('Check page content', async () => {
        render(<SecurityPage activeUserId={'userId'} />);

        expect(screen.getByText('Password')).toBeInTheDocument();
        expect(screen.getByText('Change password')).toBeInTheDocument();
        expect(
            screen.getByText('Set a unique password to protect your personal Intel® Geti™ account.')
        ).toBeInTheDocument();
    });
});
