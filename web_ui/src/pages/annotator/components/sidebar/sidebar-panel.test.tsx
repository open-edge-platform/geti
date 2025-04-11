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

import { fireEvent, screen } from '@testing-library/react';

import { getImageData } from '../../../../shared/canvas-utils';
import { ViewModes } from '../../../../shared/components/media-view-modes/utils';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { getMockedImage } from '../../../../test-utils/utils';
import { ANNOTATOR_MODE, ToolType } from '../../core/annotation-tool-context.interface';
import { AnalyticsAnnotationSceneProvider } from '../../providers/analytics-annotation-scene-provider/analytics-annotation-scene-provider.component';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { AnnotationThresholdProvider } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { DatasetProvider } from '../../providers/dataset-provider/dataset-provider.component';
import { PredictionProvider } from '../../providers/prediction-provider/prediction-provider.component';
import { DefaultSelectedMediaItemProvider } from '../../providers/selected-media-item-provider/default-selected-media-item-provider.component';
import { SubmitAnnotationsProvider } from '../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { TaskChainProvider } from '../../providers/task-chain-provider/task-chain-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { SidebarPanel } from './sidebar-panel.component';

const mockROI = { x: 0, y: 0, height: 100, width: 100 };
const mockImage = getMockedImage(mockROI);

const mockedUserProjectSettings = getMockedUserProjectSettingsObject();

jest.mock('../../providers/region-of-interest-provider/region-of-interest-provider.component', () => ({
    ...jest.requireActual('../../providers/region-of-interest-provider/region-of-interest-provider.component'),
    useROI: jest.fn(() => ({
        roi: mockROI,
        image: mockImage,
    })),
}));

jest.mock('../../providers/annotator-provider/annotator-provider.component', () => ({
    ...jest.requireActual('../../providers/annotator-provider/annotator-provider.component'),
    useAnnotator: jest.fn(() => ({
        selectedMediaItem: {},
        userProjectSettings: mockedUserProjectSettings,
    })),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

const App = ({
    showDatasetPanel = false,
    showCountingPanel = false,
    showAnnotationsPanel = false,
}: {
    showDatasetPanel?: boolean;
    showCountingPanel?: boolean;
    showAnnotationsPanel?: boolean;
}) => {
    const image = document.createElement('img');
    const mediaItem = getMockedImageMediaItem(image);
    const annotationToolContext = fakeAnnotationToolContext({ mode: ANNOTATOR_MODE.ACTIVE_LEARNING });
    jest.mocked(useAnnotationToolContext).mockImplementation(() => annotationToolContext);

    return (
        <AnnotationSceneProvider annotations={[]} labels={[]}>
            <TaskProvider>
                <DatasetProvider>
                    <DefaultSelectedMediaItemProvider
                        selectedMediaItem={{
                            ...mediaItem,
                            annotations: [],
                            predictions: undefined,
                            image: getImageData(image),
                        }}
                    >
                        <AnalyticsAnnotationSceneProvider activeTool={ToolType.BoxTool}>
                            <TaskChainProvider tasks={[]} selectedTask={null} defaultLabel={null}>
                                <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                                    <PredictionProvider
                                        settings={getMockedUserProjectSettingsObject()}
                                        explanations={[]}
                                        initPredictions={[]}
                                        userAnnotationScene={annotationToolContext.scene}
                                    >
                                        <SubmitAnnotationsProvider
                                            settings={getMockedUserProjectSettingsObject()}
                                            annotations={[]}
                                            saveAnnotations={jest.fn()}
                                            currentMediaItem={undefined}
                                            discardAnnotations={jest.fn()}
                                        >
                                            <SidebarPanel
                                                showDatasetPanel={showDatasetPanel}
                                                showCountingPanel={showCountingPanel}
                                                showAnnotationPanel={showAnnotationsPanel}
                                                annotationToolContext={annotationToolContext}
                                                datasetViewMode={ViewModes.SMALL}
                                                setDatasetViewMode={jest.fn()}
                                            />
                                        </SubmitAnnotationsProvider>
                                    </PredictionProvider>
                                </AnnotationThresholdProvider>
                            </TaskChainProvider>
                        </AnalyticsAnnotationSceneProvider>
                    </DefaultSelectedMediaItemProvider>
                </DatasetProvider>
            </TaskProvider>
        </AnnotationSceneProvider>
    );
};

describe('Sidebar', () => {
    it('Shows dataset panel', async () => {
        await render(<App showDatasetPanel />);

        expect(screen.queryByRole('button', { name: 'annotation list' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'annotation list count' })).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'dataset accordion' }));
        expect(screen.getByRole('button', { name: /Choose annotation dataset/ })).toBeInTheDocument();
    });

    it('Shows the annotation list panel', async () => {
        await render(<App showAnnotationsPanel />);

        expect(screen.queryByRole('button', { name: 'annotation list count' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Choose annotation dataset/ })).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'annotation list' }));
        expect(screen.getByRole('heading', { name: 'Annotations' })).toBeInTheDocument();
    });

    it('Shows a counting panel', async () => {
        await render(<App showCountingPanel />);

        expect(screen.queryByRole('button', { name: 'annotation list' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Choose annotation dataset/ })).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'annotation list count' }));
        expect(screen.getByRole('heading', { name: 'Counting' })).toBeInTheDocument();
    });
});
