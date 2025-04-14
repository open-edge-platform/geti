// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { Explanation } from '../../../../core/annotations/prediction.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { labelFromModel, labelFromUser } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { CANVAS_ADJUSTMENTS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { initialCanvasConfig } from '../../../../core/user-settings/utils';
import { fakeAnnotationToolContext } from '../../../../test-utils/fake-annotator-context';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { checkSpectrumButtonTooltip, checkTooltip } from '../../../../test-utils/utils';
import {
    useStreamingVideoPlayer,
    VideoPlayerPlayerContextProps,
} from '../../components/video-player/streaming-video-player/streaming-video-player-provider.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useAnnotatorCanvasSettings } from '../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import {
    ExplanationOpacityProvider,
    PredictionContextProps,
    usePrediction,
} from '../../providers/prediction-provider/prediction-provider.component';
import { TaskContextProps, useTask } from '../../providers/task-provider/task-provider.component';
import { ExplanationSecondaryToolbar, KEYPOINT_DISABLE_MESSAGE } from './explanation-secondary-toolbar.component';
import { formatExplanations, OVERLAP_LABEL_OPACITY } from './explanation-toolbar.component';

const mockMapRoi = {
    id: '123',
    shape: {
        y: 0,
        x: 0,
        type: 'RECTANGLE',
        height: 0,
        width: 0,
    },
};

const mockLabels = [
    labelFromUser(getMockedLabel({ name: 'label-1', id: '1111' })),
    labelFromUser(getMockedLabel({ name: 'label-2', id: '2222' })),
    labelFromUser(getMockedLabel({ name: 'label-3', id: '3333' })),
    labelFromUser(getMockedLabel({ name: 'label-4', id: '4444' })),
    labelFromUser(getMockedLabel({ name: 'label-5', id: '5555' })),
];

const mockExplanations: Explanation[] = [
    {
        id: '6138bca43b7b11505c43f2c1',
        labelsId: mockLabels[0].id,
        name: 'Lorem',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/600/400',
    },
    {
        id: '6138bca43b7b11505c43f2c2',
        labelsId: mockLabels[1].id,
        name: 'Ipsum',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/700/500',
    },
    {
        id: '6138bca43b7b11505c43f2c3',
        labelsId: mockLabels[2].id,
        name: 'Dolor',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/800/600',
    },
    {
        id: '6138bca43b7b11505c43f2c4',
        labelsId: mockLabels[3].id,
        name: 'Sit',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/900/700',
    },
    {
        id: '6138bca43b7b11505c43f2c5',
        labelsId: mockLabels[4].id,
        name: 'Amet',
        roi: mockMapRoi,
        url: 'https://placekitten.com/g/1000/800',
    },
];

jest.mock('../../providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('../../providers/prediction-provider/prediction-provider.component'),
    usePrediction: jest.fn(),
}));

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../components/video-player/streaming-video-player/streaming-video-player-provider.component', () => ({
    ...jest.requireActual(
        '../../components/video-player/streaming-video-player/streaming-video-player-provider.component'
    ),
    useStreamingVideoPlayer: jest.fn(),
}));

jest.mock('../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component', () => ({
    ...jest.requireActual(
        '../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component'
    ),
    useAnnotatorCanvasSettings: jest.fn(),
}));

const renderApp = (
    tasksHook: Partial<TaskContextProps> = {},
    predictionOptions?: Partial<PredictionContextProps>,
    isPlaying = false
) => {
    jest.mocked(usePrediction).mockReturnValue({
        explanations: mockExplanations,
        isExplanationVisible: true,
        setExplanationVisible: jest.fn(),
        setSelectedExplanation: jest.fn(),
        selectedExplanation: mockExplanations[0],
        predictionAnnotations: [],
        ...predictionOptions,
    } as unknown as PredictionContextProps);

    jest.mocked(useTask).mockReturnValue(mockedTaskContextProps(tasksHook));
    jest.mocked(useStreamingVideoPlayer).mockReturnValue({ isPlaying } as VideoPlayerPlayerContextProps);

    return render(
        <ExplanationOpacityProvider>
            <ExplanationSecondaryToolbar />
        </ExplanationOpacityProvider>
    );
};

const emptyLabel = getMockedLabel({ isEmpty: true, name: 'No object' });
const noObjectPrediction = getMockedAnnotation(
    {
        id: 'test-prediction-annotation',
        labels: [labelFromModel(emptyLabel, 0.8, '123', '321')],
    },
    ShapeType.Rect
);

describe('ExplanationSecondaryToolbar', () => {
    beforeEach(() => {
        jest.useRealTimers();

        jest.mocked(useAnnotationToolContext).mockImplementation(() => fakeAnnotationToolContext({}));

        jest.mocked(useAnnotatorCanvasSettings).mockReturnValue({
            handleSaveConfig: jest.fn(),
            canvasSettingsState: [initialCanvasConfig, jest.fn()],
        });
    });

    it('empty explanations', async () => {
        await renderApp({ tasks: [getMockedTask({ labels: mockLabels })] }, { explanations: [] });

        expect(screen.queryByRole('switch', { name: /overlap annotations/ })).toBeDisabled();
        expect(screen.queryByRole('switch', { name: /explanation\-switcher/i })).toBeDisabled();
    });

    it('video playing disables explanation switcher', async () => {
        const mockSetSelectedExplanation = jest.fn();
        const task = getMockedTask({ labels: mockLabels });

        await renderApp(
            { tasks: [task], selectedTask: task },
            { setSelectedExplanation: mockSetSelectedExplanation, explanations: mockExplanations },
            true
        );

        expect(screen.queryByRole('switch', { name: /explanation\-switcher/i })).toBeDisabled();
    });

    it('should show explanation description on hover over the toggle label', async () => {
        await renderApp({ tasks: [getMockedTask({ labels: mockLabels })] }, { explanations: mockExplanations });

        await checkSpectrumButtonTooltip(
            screen.getByLabelText('explanation-switcher'),
            /The explanation map visually highlights/i
        );
    });

    it('renders map picker correctly', async () => {
        const mockSetSelectedExplanation = jest.fn();
        await renderApp(
            { tasks: [getMockedTask({ labels: mockLabels })] },
            { setSelectedExplanation: mockSetSelectedExplanation }
        );

        await waitFor(() => {
            screen.getByTestId('show-explanations-dropdown');
        });

        fireEvent.click(screen.getByTestId('show-explanations-dropdown'));

        const [firstLabel, ...otherLabels] = mockLabels;
        expect(screen.getByRole('option', { name: firstLabel.name })).toBeInTheDocument();

        otherLabels.forEach(({ name }) => {
            expect(screen.getByRole('option', { name })).toBeInTheDocument();
        });

        const formattedMockedExplanations = formatExplanations(mockLabels, mockExplanations);
        const [firstExplanation] = formattedMockedExplanations;

        fireEvent.click(screen.getByRole('option', { name: firstLabel.name }));

        expect(mockSetSelectedExplanation).toHaveBeenCalledWith(firstExplanation);
    });

    it('renders opacity slider correctly', async () => {
        await renderApp({ tasks: [getMockedTask({ labels: mockLabels })] });

        const slider = screen.getByRole('button', { name: /opacity button/ });
        expect(slider).toBeInTheDocument();
        expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it.each([
        [DOMAIN.CLASSIFICATION, 'Explanation'],
        [DOMAIN.DETECTION, 'Explanation'],
        [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX, 'Explanation'],
        [DOMAIN.SEGMENTATION, 'Explanation'],
        [DOMAIN.SEGMENTATION_INSTANCE, 'Explanation'],
        [DOMAIN.ANOMALY_CLASSIFICATION, 'Explanation'],
        [DOMAIN.ANOMALY_DETECTION, 'Explanation'],
        [DOMAIN.ANOMALY_SEGMENTATION, 'Explanation'],
    ])('%o shows %o', async (domain: DOMAIN, explanationName: string) => {
        const task = getMockedTask({ domain });

        await renderApp({ tasks: [task], selectedTask: task });

        screen.getByText(explanationName);

        expect(screen.getByText(explanationName)).toBeInTheDocument();
    });

    it('format map with label name', () => {
        const [firstMockedExplanation] = mockExplanations;
        const emptyLabelName = { ...firstMockedExplanation, labelsId: '' };

        expect(formatExplanations(mockLabels, mockExplanations)).toEqual(
            expect.arrayContaining([
                expect.objectContaining({ labelName: mockLabels[0].name }),
                expect.objectContaining({ labelName: mockLabels[1].name }),
                expect.objectContaining({ labelName: mockLabels[2].name }),
                expect.objectContaining({ labelName: mockLabels[3].name }),
                expect.objectContaining({ labelName: mockLabels[4].name }),
            ])
        );

        expect(formatExplanations(mockLabels, [emptyLabelName])).toEqual(
            expect.arrayContaining([expect.objectContaining({ labelName: emptyLabelName.name })])
        );
    });

    it('is disabled for keypoint detection projects', async () => {
        await renderApp({ tasks: [getMockedTask({ domain: DOMAIN.KEYPOINT_DETECTION })] }, { explanations: [] });

        const switcher = screen.getByRole('switch', { name: /explanation\-switcher/i });
        expect(switcher).toBeDisabled();

        await checkTooltip(screen.getByLabelText('disabled tooltip trigger'), KEYPOINT_DISABLE_MESSAGE);
    });

    describe('overlap annotation toggle', () => {
        it('empty explanations and "empty label" predictions render overlap annotations', async () => {
            await renderApp(
                { tasks: [getMockedTask({ labels: mockLabels })] },
                { explanations: [], predictionAnnotations: [noObjectPrediction] }
            );

            expect(screen.queryByRole('switch', { name: /explanation\-switcher/i })).toBeDisabled();
            expect(screen.queryByRole('switch', { name: /overlap annotations/ })).toBeVisible();
        });

        it('renders overlap annotations', async () => {
            await renderApp({ tasks: [getMockedTask({ labels: mockLabels })] });

            const slider = screen.getByRole('switch', { name: /overlap annotations/i });
            expect(slider).toBeInTheDocument();
            expect(slider).toBeDisabled();
        });

        it('updates label opacity', async () => {
            const mockedHandleCanvasSetting = jest.fn();

            jest.mocked(useAnnotatorCanvasSettings).mockReturnValue({
                canvasSettingsState: [initialCanvasConfig, mockedHandleCanvasSetting],
                handleSaveConfig: jest.fn(),
            });

            await renderApp({ tasks: [getMockedTask({ labels: mockLabels })] }, { isExplanationVisible: false });

            const slider = screen.getByRole('switch', { name: /overlap annotations/ });
            expect(slider).toBeInTheDocument();
            await userEvent.click(slider);

            expect(mockedHandleCanvasSetting).toHaveBeenLastCalledWith(
                CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY,
                OVERLAP_LABEL_OPACITY
            );

            await userEvent.click(slider);
            expect(mockedHandleCanvasSetting).toHaveBeenLastCalledWith(
                CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY,
                initialCanvasConfig[CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY].defaultValue
            );
        });
    });
});
