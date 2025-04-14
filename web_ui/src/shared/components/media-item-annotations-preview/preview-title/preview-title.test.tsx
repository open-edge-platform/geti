// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { PreviewTitle } from './preview-title.component';

describe('PreviewTitle component', () => {
    it('Check if title is displayed on the screen', async () => {
        render(<PreviewTitle title={'Main title'} subTitle={'Sub title'} />);

        expect(screen.getByTestId('preview-title')).toBeInTheDocument();
    });
});
