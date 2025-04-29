// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../core/projects/services/project-service.interface';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedDatasetIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { AnnotatorProviders } from '../../test-utils/annotator-render';
import { SelectingStateProvider } from '../../tools/selecting-tool/selecting-state-provider.component';
import { TransformZoomAnnotation } from '../../zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../zoom/zoom-provider.component';
import { AnnotationToolProvider } from '../annotation-tool-provider/annotation-tool-provider.component';
import { AnnotatorContextMenuProvider, useAnnotatorContextMenu } from './annotator-context-menu-provider.component';
import { useToolContextMenu } from './use-tool-context-menu.hook';
import { ToolContextMenuItemsKeys } from './utils';

jest.mock('./annotator-context-menu-provider.component', () => ({
    ...jest.requireActual('./annotator-context-menu-provider.component'),
    useAnnotatorContextMenu: jest.fn(),
}));

const renderApp = async ({
    showContextMenu = jest.fn(),
    projectService = createInMemoryProjectService(),
}: {
    showContextMenu?: jest.Mock;
    projectService?: ProjectService;
}) => {
    const annotationToolContext = fakeAnnotationToolContext({});
    jest.mocked(useAnnotatorContextMenu).mockImplementation(() => ({
        showContextMenu,
        hideContextMenu: jest.fn(),
        contextConfig: {
            contextId: null,
            handleMenuAction: jest.fn(),
            ariaLabel: '',
            menuItems: [],
            menuPosition: { top: 0, left: 0 },
        },
    }));

    const response = renderHookWithProviders(() => useToolContextMenu({ annotationToolContext }), {
        wrapper: ({ children }) => (
            <AnnotatorProviders datasetIdentifier={getMockedDatasetIdentifier()}>
                <AnnotationToolProvider>
                    <SelectingStateProvider>
                        <ZoomProvider>
                            <TransformZoomAnnotation>
                                <AnnotatorContextMenuProvider>{children}</AnnotatorContextMenuProvider>
                            </TransformZoomAnnotation>
                        </ZoomProvider>
                    </SelectingStateProvider>
                </AnnotationToolProvider>
            </AnnotatorProviders>
        ),
        providerProps: { projectService },
    });

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return response;
};

describe('useToolContextMenu', () => {
    it('disable hide/show annotation with keypoint detection', async () => {
        const mockedShowContextMenu = jest.fn();
        const projectService = createInMemoryProjectService();

        projectService.getProject = async () =>
            getMockedProject({
                tasks: [getMockedTask({ domain: DOMAIN.KEYPOINT_DETECTION })],
            });

        const { result } = await renderApp({ projectService, showContextMenu: mockedShowContextMenu });

        result.current.handleShowToolContextMenu({ x: 1, y: 2 });

        expect(mockedShowContextMenu).toHaveBeenCalledWith(
            expect.objectContaining({
                disabledKeys: expect.arrayContaining([
                    ToolContextMenuItemsKeys.HIDE_ANNOTATIONS,
                    ToolContextMenuItemsKeys.SHOW_ANNOTATIONS,
                ]),
            })
        );
    });
});
