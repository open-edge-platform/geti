// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { Explanation } from '../../../../core/annotations/prediction.interface';
import { labelFromUser } from '../../../../core/annotations/utils';
import { initialCanvasConfig } from '../../../../core/user-settings/utils';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedExplanation } from '../../../../test-utils/mocked-items-factory/mocked-explanation';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { checkSpectrumButtonTooltip } from '../../../../test-utils/utils';
import { useAnnotatorCanvasSettings } from '../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import {
    ExplanationOpacityProvider,
    PredictionContextProps,
    usePrediction,
} from '../../providers/prediction-provider/prediction-provider.component';
import { ExplanationPreviewToolbar, ExplanationPreviewToolbarProps } from './explanation-preview-toolbar.component';

const mockExplanations: Explanation[] = [getMockedExplanation()];

jest.mock('../../providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('../../providers/prediction-provider/prediction-provider.component'),
    usePrediction: jest.fn(),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => mockedTaskContextProps({ tasks: [] })),
}));

const mockedToolContext = fakeAnnotationToolContext({});
jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(() => mockedToolContext),
}));

jest.mock('../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component', () => ({
    ...jest.requireActual(
        '../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component'
    ),
    useAnnotatorCanvasSettings: jest.fn(),
}));

const renderApp = (
    staticExplanationsOptions: ExplanationPreviewToolbarProps,
    predictionOptions?: Partial<PredictionContextProps>
) => {
    jest.mocked(usePrediction).mockReturnValue({
        setSelectedExplanation: jest.fn(),
        predictionAnnotations: [],
        ...predictionOptions,
    } as unknown as PredictionContextProps);

    return render(
        <ExplanationOpacityProvider>
            <ExplanationPreviewToolbar {...staticExplanationsOptions} />
        </ExplanationOpacityProvider>
    );
};

describe('ExplanationPreviewToolbar', () => {
    beforeEach(() => {
        jest.mocked(useAnnotatorCanvasSettings).mockReturnValue({
            handleSaveConfig: jest.fn(),
            canvasSettingsState: [initialCanvasConfig, jest.fn()],
        });
    });

    it('render static explanations and selects the first one', async () => {
        const mockSetSelectedExplanation = jest.fn();
        const label = labelFromUser(
            getMockedLabel({ name: 'static-explanation-test-label', id: 'static-explanation-test-label' })
        );
        const staticExplanation = { ...mockExplanations[0], id: 'static-explanation-test-id', labelsId: label.id };

        await renderApp(
            { explanations: [staticExplanation], selectedExplanation: staticExplanation },
            { setSelectedExplanation: mockSetSelectedExplanation }
        );

        expect(screen.getByRole('button', { name: /show explanations dropdown/i })).toBeVisible();
        expect(mockSetSelectedExplanation).toHaveBeenNthCalledWith(1, staticExplanation);
    });

    it('should show explanation description on hover over the toggle label', async () => {
        const mockSetSelectedExplanation = jest.fn();
        const label = labelFromUser(
            getMockedLabel({ name: 'static-explanation-test-label', id: 'static-explanation-test-label' })
        );
        const staticExplanation = { ...mockExplanations[0], id: 'static-explanation-test-id', labelsId: label.id };

        await renderApp(
            { explanations: [staticExplanation], selectedExplanation: staticExplanation },
            { setSelectedExplanation: mockSetSelectedExplanation }
        );

        await checkSpectrumButtonTooltip(
            screen.getByLabelText('explanation-switcher'),
            /The explanation map visually highlights/i
        );
    });
});
