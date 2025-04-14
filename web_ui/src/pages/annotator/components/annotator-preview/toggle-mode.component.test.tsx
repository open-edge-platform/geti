// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedUserProjectSettingsObject } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { checkSpectrumButtonTooltip } from '../../../../test-utils/utils';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { AnnotationSceneProvider } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { PredictionProvider } from '../../providers/prediction-provider/prediction-provider.component';
import { SelectedMediaItemProvider } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { TaskChainProvider } from '../../providers/task-chain-provider/task-chain-provider.component';
import { TaskProvider } from '../../providers/task-provider/task-provider.component';
import { ToggleMode } from './toggle-mode.component';

describe('ToggleMode', () => {
    const renderApp = (setMode = jest.fn()) => {
        const annotationToolContext = fakeAnnotationToolContext({ mode: ANNOTATOR_MODE.ACTIVE_LEARNING });

        render(
            <AnnotationSceneProvider annotations={annotationToolContext.scene.annotations} labels={[]}>
                <TaskProvider>
                    <SelectedMediaItemProvider>
                        <TaskChainProvider tasks={[]} selectedTask={null} defaultLabel={null}>
                            <PredictionProvider
                                settings={getMockedUserProjectSettingsObject()}
                                explanations={[]}
                                initPredictions={[]}
                                userAnnotationScene={annotationToolContext.scene}
                            >
                                <ToggleMode mode={ANNOTATOR_MODE.ACTIVE_LEARNING} setMode={setMode} />
                            </PredictionProvider>
                        </TaskChainProvider>
                    </SelectedMediaItemProvider>
                </TaskProvider>
            </AnnotationSceneProvider>
        );
    };
    it('annotation mode', async () => {
        const setMode = jest.fn();
        renderApp(setMode);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        await checkSpectrumButtonTooltip(
            screen.getByRole('button', { name: /select annotation mode/i }),
            'User annotation mode'
        );

        expect(setMode).toHaveBeenCalledWith(ANNOTATOR_MODE.ACTIVE_LEARNING);
    });

    it('predictions mode', async () => {
        const setMode = jest.fn();
        renderApp(setMode);

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        await checkSpectrumButtonTooltip(
            screen.getByRole('button', { name: /select prediction mode/i }),
            'AI prediction mode'
        );

        expect(setMode).toHaveBeenCalledWith(ANNOTATOR_MODE.PREDICTION);
    });
});
