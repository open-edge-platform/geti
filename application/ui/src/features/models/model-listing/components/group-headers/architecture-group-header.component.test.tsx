// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import { render } from 'test-utils/render';

import { getMockedModelArchitecture } from '../../../../../../mocks/mock-model';
import { ArchitectureGroupHeader } from './architecture-group-header.component';

describe('ArchitectureGroupHeader', () => {
    it('renders the architecture name and a link to its license', () => {
        const architecture = getMockedModelArchitecture();

        render(<ArchitectureGroupHeader architecture={architecture} />);

        expect(screen.getByRole('heading', { name: architecture.name })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: architecture.license.name })).toHaveAttribute(
            'href',
            architecture.license.url
        );
    });

    it('renders the license name as plain text when it has no url', () => {
        const architecture = getMockedModelArchitecture({ license: { name: 'varies by model', url: '' } });

        render(<ArchitectureGroupHeader architecture={architecture} />);

        expect(screen.getByText('varies by model', { exact: false })).toBeInTheDocument();
        expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });
});
