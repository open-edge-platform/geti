// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Annotation } from '../../../../../../core/annotations/annotation.interface';
import { Label } from '../../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../../core/projects/core.interface';
import { applicationRender as render } from '../../../../../../test-utils/application-provider-render';
import { fakeAnnotationToolContext } from '../../../../../../test-utils/fake-annotator-context';
import { getMockedProjectIdentifier } from '../../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import {
    getMockedProject,
    mockedProjectContextProps,
} from '../../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedUserProjectSettingsObject } from '../../../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedTask } from '../../../../../../test-utils/mocked-items-factory/mocked-tasks';
import {
    ProjectProvider,
    useProject,
} from '../../../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationScene } from '../../../../core/annotation-scene.interface';
import { AnnotationToolContext, ToolType } from '../../../../core/annotation-tool-context.interface';
import { AnnotationSceneProvider } from '../../../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { EMPTY_ANNOTATIONS, EMPTY_EXPLANATION } from '../../../../providers/annotator-provider/utils';
import { PredictionProvider } from '../../../../providers/prediction-provider/prediction-provider.component';
import { SelectedMediaItemProvider } from '../../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskChainProvider } from '../../../../providers/task-chain-provider/task-chain-provider.component';
import { TaskProvider, useTask } from '../../../../providers/task-provider/task-provider.component';
import { LabelsShortcuts } from '../labels-shortcuts.component';

export const renderApp = async ({
    annotations,
    labels,
    tool,
    isDrawing = false,
    domain = DOMAIN.SEGMENTATION,
    addLabel = jest.fn(),
    removeLabels = jest.fn(),
    updateToolSettings = jest.fn(),
    removeAnnotations = jest.fn(),
}: {
    annotations: Annotation[];
    labels: Label[];
    tool?: ToolType;
    isDrawing?: boolean;
    domain?: DOMAIN;
    addLabel?: AnnotationScene['addLabel'];
    removeLabels?: AnnotationScene['removeLabels'];
    updateToolSettings?: AnnotationToolContext['updateToolSettings'];
    removeAnnotations?: AnnotationScene['removeAnnotations'];
}) => {
    jest.mocked(useProject).mockReturnValue(
        mockedProjectContextProps({
            project: getMockedProject({ tasks: [getMockedTask({ domain, labels })] }),
        })
    );

    const annotationToolContext = fakeAnnotationToolContext({
        annotations,
        addLabel,
        removeLabels,
        tool,
        updateToolSettings,
        isDrawing,
        removeAnnotations,
    });

    const segmentationMockedTask = getMockedTask({ domain, labels });

    const container = await render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <SelectedMediaItemProvider>
                    <AnnotationSceneProvider annotations={annotations} labels={labels}>
                        <TaskChainProvider
                            tasks={[segmentationMockedTask]}
                            selectedTask={segmentationMockedTask}
                            defaultLabel={null}
                        >
                            <PredictionProvider
                                explanations={EMPTY_EXPLANATION}
                                userAnnotationScene={annotationToolContext.scene}
                                initPredictions={EMPTY_ANNOTATIONS}
                                settings={getMockedUserProjectSettingsObject()}
                            >
                                <div data-testid={'container'}>
                                    <LabelsShortcuts labels={labels} annotationToolContext={annotationToolContext} />
                                </div>
                            </PredictionProvider>
                        </TaskChainProvider>
                    </AnnotationSceneProvider>
                </SelectedMediaItemProvider>
            </TaskProvider>
        </ProjectProvider>
    );
    return container;
};

const DefaultLabel = () => {
    const { defaultLabel } = useTask();

    return <div aria-label='Default label'>{defaultLabel?.id}</div>;
};
export const renderAppWithDefaultLabel = async (
    annotation: Annotation[],
    labels: Label[],
    annotationToolContext = fakeAnnotationToolContext()
) => {
    await render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TaskProvider>
                <div data-testid={'container'}>
                    <AnnotationSceneProvider annotations={annotation} labels={labels}>
                        <LabelsShortcuts labels={labels} annotationToolContext={annotationToolContext} />
                    </AnnotationSceneProvider>
                </div>
                <DefaultLabel />
            </TaskProvider>
        </ProjectProvider>
    );
};
