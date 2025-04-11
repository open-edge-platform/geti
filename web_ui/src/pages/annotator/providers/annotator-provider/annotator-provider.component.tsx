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

import { createContext, ReactNode, useContext, useState } from 'react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { isVideoFrame } from '../../../../core/media/video.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { useUserGlobalSettings } from '../../../../core/user-settings/hooks/use-global-settings.hook';
import { useUserProjectSettings } from '../../../../core/user-settings/hooks/use-project-settings.hook';
import {
    UserGlobalSettings,
    UserProjectSettings,
    UseSettings,
} from '../../../../core/user-settings/services/user-settings.interface';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { AskToResetFilterBeforeSubmittingAnnotations } from '../../annotation/annotation-filter/ask-to-reset-filter-before-submitting-annotations.component';
import { StreamingVideoPlayerProvider } from '../../components/video-player/streaming-video-player/streaming-video-player-provider.component';
import { VideoPlayerProvider } from '../../components/video-player/video-player-provider.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import UndoRedoProvider from '../../tools/undo-redo/undo-redo-provider.component';
import { AnalyticsAnnotationSceneProvider } from '../analytics-annotation-scene-provider/analytics-annotation-scene-provider.component';
import { AnnotationSceneContext } from '../annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotationSceneState } from '../annotation-scene-provider/use-annotation-scene-state.hook';
import { AnnotationThresholdProvider } from '../annotation-threshold-provider/annotation-threshold-provider.component';
import { AnnotatorCanvasSettingsProvider } from '../annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import { HoveredProvider } from '../hovered-provider/hovered-provider.component';
import { PredictionProvider } from '../prediction-provider/prediction-provider.component';
import { useSelectedMediaItem } from '../selected-media-item-provider/selected-media-item-provider.component';
import { SelectedProvider } from '../selected-provider/selected-provider.component';
import { SubmitAnnotationsProvider } from '../submit-annotations-provider/submit-annotations-provider.component';
import { TaskChainProvider } from '../task-chain-provider/task-chain-provider.component';
import { useTask } from '../task-provider/task-provider.component';
import { useInitialAnnotation } from './use-initial-annotations.hook';
import { usePanelsConfig } from './use-panels-config';
import { useSaveAnnotations } from './use-save-annotations.hook';
import { defaultToolForProject, EMPTY_EXPLANATION } from './utils';

export interface AnnotatorContextProps {
    userProjectSettings: UseSettings<UserProjectSettings>;
    userGlobalSettings: UseSettings<UserGlobalSettings>;
    activeTool: ToolType;
    setActiveTool: (tool: ToolType) => void;
}

const AnnotatorContext = createContext<AnnotatorContextProps | undefined>(undefined);

interface AnnotatorProviderProps {
    children: ReactNode;
}

export const AnnotatorProvider = ({ children }: AnnotatorProviderProps): JSX.Element => {
    const { useActiveUser } = useUsers();
    const saveAnnotations = useSaveAnnotations();
    const { project, projectIdentifier } = useProject();
    const { data: activeUser } = useActiveUser(projectIdentifier.organizationId);
    const { isActiveLearningMode } = useAnnotatorMode();

    const userProjectSettings = useUserProjectSettings(projectIdentifier);
    const userGlobalSettings = useUserGlobalSettings();
    const { tasks, selectedTask, defaultLabel, activeDomains, isTaskChainDomainSelected } = useTask();

    usePanelsConfig(selectedTask, tasks, userProjectSettings, projectIdentifier.projectId);

    const [activeTool, setActiveTool] = useState<ToolType>(() => defaultToolForProject(activeDomains));

    const { selectedMediaItem, predictionsQuery } = useSelectedMediaItem();
    const isTaskChainSelectedClassification = isTaskChainDomainSelected(DOMAIN.CLASSIFICATION);

    const initialPredictionAnnotations = predictionsQuery.data?.annotations;
    const initialAnnotations = useInitialAnnotation(
        selectedMediaItem,
        selectedTask,
        userProjectSettings,
        isTaskChainSelectedClassification
    );

    const { undoRedoActions, ...userAnnotationScene } = useAnnotationSceneState(
        initialAnnotations,
        project.labels,
        activeUser?.id
    );

    const saveAnnotationsAndResetState = async (annotations: ReadonlyArray<Annotation>) => {
        const newAnnotations = await saveAnnotations(annotations, selectedMediaItem as MediaItem);
        // Reset so that the user can not "undo" the saving the annotations
        undoRedoActions.reset(newAnnotations);
    };

    // In the prediction mode we only want to show the explanation toolbar and not allow
    // the user to make any changes to the annotation scene
    const activeToolBasedOnMode = isActiveLearningMode ? activeTool : ToolType.Explanation;

    return (
        <AnnotatorContext.Provider
            value={{ userProjectSettings, userGlobalSettings, activeTool: activeToolBasedOnMode, setActiveTool }}
        >
            <AnnotationSceneContext.Provider value={userAnnotationScene}>
                <UndoRedoProvider state={undoRedoActions}>
                    <TaskChainProvider tasks={tasks} selectedTask={selectedTask} defaultLabel={defaultLabel}>
                        <AnalyticsAnnotationSceneProvider activeTool={activeTool}>
                            <AnnotationThresholdProvider minThreshold={0} selectedTask={selectedTask}>
                                <PredictionProvider
                                    settings={userProjectSettings}
                                    userAnnotationScene={userAnnotationScene}
                                    initPredictions={initialPredictionAnnotations}
                                    explanations={selectedMediaItem?.predictions?.maps || EMPTY_EXPLANATION}
                                >
                                    <SubmitAnnotationsProvider
                                        settings={userProjectSettings}
                                        currentMediaItem={selectedMediaItem}
                                        discardAnnotations={undoRedoActions.reset}
                                        annotations={userAnnotationScene.annotations}
                                        saveAnnotations={saveAnnotationsAndResetState}
                                    >
                                        <AnnotatorCanvasSettingsProvider settings={userProjectSettings}>
                                            <HoveredProvider>
                                                <SelectedProvider>
                                                    <AskToResetFilterBeforeSubmittingAnnotations>
                                                        {children}
                                                    </AskToResetFilterBeforeSubmittingAnnotations>
                                                </SelectedProvider>
                                            </HoveredProvider>
                                        </AnnotatorCanvasSettingsProvider>
                                    </SubmitAnnotationsProvider>
                                </PredictionProvider>
                            </AnnotationThresholdProvider>
                        </AnalyticsAnnotationSceneProvider>
                    </TaskChainProvider>
                </UndoRedoProvider>
            </AnnotationSceneContext.Provider>
        </AnnotatorContext.Provider>
    );
};

export const MediaItemProvider = ({ children }: { children: ReactNode }): JSX.Element => {
    const { selectedMediaItem, setSelectedMediaItem } = useSelectedMediaItem();

    const isFrame = selectedMediaItem !== undefined && isVideoFrame(selectedMediaItem);
    return (
        <VideoPlayerProvider
            videoFrame={isFrame ? selectedMediaItem : undefined}
            selectVideoFrame={setSelectedMediaItem}
        >
            <StreamingVideoPlayerProvider mediaItem={isFrame ? selectedMediaItem : undefined}>
                {children}
            </StreamingVideoPlayerProvider>
        </VideoPlayerProvider>
    );
};

export const useAnnotator = (): AnnotatorContextProps => {
    const context = useContext(AnnotatorContext);

    if (context === undefined) {
        throw new MissingProviderError('useAnnotator', 'AnnotatorProvider');
    }

    return context;
};
