// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, screen } from '@testing-library/react';

import { mockedProjectContextProps } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { ProjectMediaFilterStatusList } from './project-media-filter-status-list.component';

jest.mock('../../providers/project-provider/project-provider.component', () => ({
    useProject: jest.fn(() => mockedProjectContextProps({})),
}));

describe('Project Media Filter Status List', () => {
    afterAll(() => {
        jest.clearAllMocks();
    });

    it("doesn't show partially annotated option with simple project", async () => {
        await render(<ProjectMediaFilterStatusList onSelectionChange={jest.fn()} />);

        expect(screen.getByText('Any')).toBeInTheDocument();
        expect(screen.getByText('Annotated')).toBeInTheDocument();
        expect(screen.getByText('None')).toBeInTheDocument();
        expect(screen.queryByText('Partially Annotated')).not.toBeInTheDocument();
    });

    it('shows partially annotated option when is a task chain project', async () => {
        jest.mocked(useProject).mockReturnValueOnce(mockedProjectContextProps({ isTaskChainProject: true }));

        await render(<ProjectMediaFilterStatusList onSelectionChange={jest.fn()} />);

        expect(screen.getByText('Any')).toBeInTheDocument();
        expect(screen.getByText('Annotated')).toBeInTheDocument();
        expect(screen.getByText('None')).toBeInTheDocument();
        expect(screen.queryByText('Partially Annotated')).toBeInTheDocument();
    });
});
