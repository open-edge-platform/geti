// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { MediaItem } from '../../../../core/media/media.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { annotatorRender as render } from '../../test-utils/annotator-render';
import { Footer } from './annotator-footer.component';

const mockedProjectIdentifier = getMockedProjectIdentifier({ workspaceId: 'workspace-id', projectId: 'project-id' });
jest.mock('react-zoom-pan-pinch', () => ({
    ...jest.requireActual('react-zoom-pan-pinch'),
    useControls: jest.fn(() => ({
        resetTransform: jest.fn(),
    })),
}));

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({
        project: { domains: [] },
        projectIdentifier: mockedProjectIdentifier,
        isSingleDomainProject: jest.fn(),
    })),
}));

jest.mock('../../zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1 } })),
}));

describe('Footer', () => {
    const renderApp = async (mediaItem: MediaItem, areActionsDisabled = false) => {
        await render(<Footer selectedItem={mediaItem} areActionsDisabled={areActionsDisabled} />);
    };

    const useProjectMockedCommonParameters = {
        projectIdentifier: mockedProjectIdentifier,
        isSingleDomainProject: jest.fn(),
        isTaskChainDomainProject: jest.fn(),
        score: null,
        reload: jest.fn(),
    };

    it('Displays zoom state and image metadata correctly', async () => {
        const image = document.createElement('img');
        const mockedImageItem = getMockedImageMediaItem(image);

        jest.mocked(useProject).mockImplementation(() => ({
            project: getMockedProject({
                domains: [],
            }),
            isTaskChainProject: false,
            ...useProjectMockedCommonParameters,
        }));

        await renderApp(mockedImageItem);

        expect(screen.queryByText('100%')).toBeTruthy();
        expect(
            screen.queryByText(
                `${mockedImageItem.name} (${mockedImageItem.metadata.width} px x ${mockedImageItem.metadata.height} px)`
            )
        ).toBeTruthy();

        expect(screen.getByRole('button', { name: 'Fit image to screen' })).toBeInTheDocument();
    });

    it('Displays project name if it is a task chain project', async () => {
        jest.mocked(useProject).mockImplementation(() => ({
            isTaskChainProject: true,
            project: getMockedProject({
                name: 'test project',
                domains: [DOMAIN.SEGMENTATION, DOMAIN.CLASSIFICATION],
            }),
            ...useProjectMockedCommonParameters,
        }));

        await renderApp(getMockedImageMediaItem({}));

        expect(screen.queryByText('test project')).toBeTruthy();
    });

    it('Does not display actions: fit to image', async () => {
        const image = document.createElement('img');
        const mockedImageItem = getMockedImageMediaItem(image);

        jest.mocked(useProject).mockImplementation(() => ({
            project: getMockedProject({ domains: [] }),
            isTaskChainProject: false,
            ...useProjectMockedCommonParameters,
        }));

        await renderApp(mockedImageItem, true);

        expect(screen.queryByRole('button', { name: 'Fit image to screen' })).not.toBeInTheDocument();
    });
});
