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

import { screen } from '@testing-library/react';
import { TransformComponent } from 'react-zoom-pan-pinch';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { initialAnnotatorConfig, initialConfig } from '../../../../core/user-settings/utils';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import {
    getMockedUserGlobalSettingsObject,
    getMockedUserProjectSettingsObject,
} from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { getMockedImage } from '../../../../test-utils/utils';
import { AnnotationToolContext, ANNOTATOR_MODE, ToolType } from '../../core/annotation-tool-context.interface';
import { AnalyticsAnnotationSceneProvider } from '../../providers/analytics-annotation-scene-provider/analytics-annotation-scene-provider.component';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { AnnotationThresholdProvider } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import {
    AnnotationToolProvider,
    useAnnotationToolContext,
} from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { AnnotatorContextProps, useAnnotator } from '../../providers/annotator-provider/annotator-provider.component';
import { DefaultHotkeys } from '../../providers/annotator-provider/utils';
import { DatasetProvider } from '../../providers/dataset-provider/dataset-provider.component';
import { PredictionProvider } from '../../providers/prediction-provider/prediction-provider.component';
import { DefaultSelectedMediaItemProvider } from '../../providers/selected-media-item-provider/default-selected-media-item-provider.component';
import { SelectedProvider } from '../../providers/selected-provider/selected-provider.component';
import { SubmitAnnotationsProvider } from '../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { TaskChainProvider } from '../../providers/task-chain-provider/task-chain-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { ZoomProvider } from '../../zoom/zoom-provider.component';
import { Sidebar } from './sidebar.component';

const mockROI = { x: 0, y: 0, height: 100, width: 100 };
const mockImage = getMockedImage(mockROI);

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
    })),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

const App = ({
    annotationToolContext,
    settings,
}: {
    annotationToolContext: AnnotationToolContext;
    settings?: Partial<UseSettings<UserProjectSettings>>;
}) => {
    const image = document.createElement('img');
    const mediaItem = getMockedImageMediaItem(image);
    jest.mocked(useAnnotationToolContext).mockImplementation(() => annotationToolContext);

    const mockSettings = getMockedUserProjectSettingsObject({
        ...settings,
    });

    return (
        <AnnotationSceneProvider annotations={[]} labels={[]}>
            <ZoomProvider>
                <TaskProvider>
                    <DatasetProvider>
                        <DefaultSelectedMediaItemProvider
                            selectedMediaItem={{
                                ...mediaItem,
                                annotations: [],
                                predictions: undefined,
                                image: getMockedImage(),
                            }}
                        >
                            <AnalyticsAnnotationSceneProvider activeTool={ToolType.BoxTool}>
                                <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                                    <TaskChainProvider tasks={[]} selectedTask={null} defaultLabel={null}>
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
                                                <AnnotationToolProvider>
                                                    <SelectedProvider>
                                                        <Sidebar
                                                            settings={mockSettings}
                                                            annotationToolContext={annotationToolContext}
                                                        />
                                                    </SelectedProvider>
                                                    <TransformComponent>{''}</TransformComponent>
                                                </AnnotationToolProvider>
                                            </SubmitAnnotationsProvider>
                                        </PredictionProvider>
                                    </TaskChainProvider>
                                </AnnotationThresholdProvider>
                            </AnalyticsAnnotationSceneProvider>
                        </DefaultSelectedMediaItemProvider>
                    </DatasetProvider>
                </TaskProvider>
            </ZoomProvider>
        </AnnotationSceneProvider>
    );
};

describe('Sidebar', () => {
    jest.mocked(useAnnotator).mockImplementation(
        () =>
            ({
                hotKeys: DefaultHotkeys,
                userProjectSettings: getMockedUserProjectSettingsObject({}),
                userGlobalSettings: getMockedUserGlobalSettingsObject({}),
            }) as unknown as AnnotatorContextProps
    );

    it('should render AnnotationList accordion if "annotation panel" is enabled and if it is a single task and not classification or anomaly project', async () => {
        const fakeContext = fakeAnnotationToolContext({ mode: ANNOTATOR_MODE.ACTIVE_LEARNING });

        // Annotation panel is enabled by default on the settings
        await render(<App annotationToolContext={fakeContext} />);

        expect(screen.getByTestId('annotation-list-accordion')).toBeInTheDocument();
        expect(screen.queryByTestId('anomaly-accordion')).toBeFalsy();
        expect(screen.queryByTestId('prediction-accordion')).toBeFalsy();
    });

    it('should NOT render AnnotationList accordion if "annotation panel" is disabled on user settings', async () => {
        const mockConfig: UserProjectSettings = {
            ...initialConfig,
            [FEATURES_KEYS.ANNOTATION_PANEL]: { ...initialAnnotatorConfig.annotation, isEnabled: false },
            [FEATURES_KEYS.COUNTING_PANEL]: { ...initialAnnotatorConfig.counting, isEnabled: false },
        };
        const mockSettings = {
            config: mockConfig,
        };

        const fakeContext = fakeAnnotationToolContext({ mode: ANNOTATOR_MODE.ACTIVE_LEARNING });

        await render(<App settings={mockSettings} annotationToolContext={fakeContext} />);

        expect(screen.queryByTestId('annotation-list-accordion')).toBeFalsy();
    });

    it('should NOT render AnnotationListCounting if "counting panel" is disabled on user settings', async () => {
        const mockConfig: UserProjectSettings = {
            ...initialConfig,
            [FEATURES_KEYS.ANNOTATION_PANEL]: { ...initialAnnotatorConfig.annotation, isEnabled: true },
            [FEATURES_KEYS.COUNTING_PANEL]: { ...initialAnnotatorConfig.counting, isEnabled: false },
        };
        const mockSettings = {
            config: mockConfig,
        };

        const fakeContext = fakeAnnotationToolContext({
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
        });

        await render(<App annotationToolContext={fakeContext} settings={mockSettings} />);

        expect(screen.queryByTestId('annotation-counting-list')).toBeFalsy();
    });

    it('should render AnnotationListCounting if "counting panel" is enabled on user settings', async () => {
        const mockConfig: UserProjectSettings = {
            ...initialConfig,
            [FEATURES_KEYS.ANNOTATION_PANEL]: { ...initialAnnotatorConfig.annotation, isEnabled: true },
            [FEATURES_KEYS.COUNTING_PANEL]: { ...initialAnnotatorConfig.counting, isEnabled: true },
        };
        const mockSettings = {
            config: mockConfig,
        };

        const fakeContext = fakeAnnotationToolContext({
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
        });

        await render(<App annotationToolContext={fakeContext} settings={mockSettings} />);

        expect(screen.getByTestId('annotation-counting-list')).toBeInTheDocument();
    });

    it('should not render "annotation panel" by default if we are on a classification task', async () => {
        const mockTask = getMockedTask({ domain: DOMAIN.CLASSIFICATION });
        const fakeContext = fakeAnnotationToolContext({
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
            selectedTask: mockTask,
            tasks: [mockTask],
        });

        await render(<App annotationToolContext={fakeContext} settings={{ config: initialConfig }} />);

        expect(screen.queryByTestId('annotation-counting-list')).not.toBeInTheDocument();
    });
});
