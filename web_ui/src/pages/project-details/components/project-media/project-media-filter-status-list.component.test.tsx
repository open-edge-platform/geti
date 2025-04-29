// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
