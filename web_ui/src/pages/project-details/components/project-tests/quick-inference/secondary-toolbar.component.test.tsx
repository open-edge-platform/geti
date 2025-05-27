// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ApplicationServicesProvider } from '@geti/core/src/services/application-services-provider.component';
import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { createInMemoryInferenceService } from '../../../../../core/annotations/services/in-memory-inference-service';
import { Label } from '../../../../../core/labels/label.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { initialConfig } from '../../../../../core/user-settings/utils';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedUserProjectSettingsObject } from '../../../../../test-utils/mocked-items-factory/mocked-settings';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { AnnotatorCanvasSettingsProvider } from '../../../../annotator/providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { QuickInferenceContextProps, useQuickInference } from './quick-inference-provider.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

const defaultSettings = getMockedUserProjectSettingsObject({
    saveConfig: jest.fn(),
    isSavingConfig: false,
    config: initialConfig,
});

const mockedInferenceService = createInMemoryInferenceService();
mockedInferenceService.getExplanationsForFile = jest.fn();
mockedInferenceService.getPredictionsForFile = jest.fn();

const emptyLabel = getMockedLabel({ id: '321', name: 'Empty', isEmpty: true });
const emptyAnnotation = getMockedAnnotation({ labels: [{ ...emptyLabel, source: {} }] });

const getExplanation = (id = '123321', labelsId: string) => ({
    id,
    url: '',
    name: '',
    labelsId,
    roi: {
        id: '134a875b-a8c8-4f94-a6b0-b0416ec7f821',
        shape: {
            x: 0,
            y: 0,
            width: 1280,
            height: 720,
            type: '1',
        },
    },
    binary: 'img-test',
});

jest.mock('./quick-inference-provider.component', () => ({
    ...jest.requireActual('./quick-inference-provider.component'),
    useQuickInference: jest.fn(),
}));

const mockedProjectService = createInMemoryProjectService();

const renderApp = async ({
    shouldShowExplanation = true,
    labels = [],
}: {
    shouldShowExplanation?: boolean;
    labels?: Label[];
}) => {
    const response = render(
        <ApplicationServicesProvider useInMemoryEnvironment inferenceService={mockedInferenceService}>
            <ProjectProvider
                projectIdentifier={{
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                    organizationId: 'organization-id',
                }}
            >
                <AnnotatorCanvasSettingsProvider settings={defaultSettings}>
                    <SecondaryToolbar labels={labels} shouldShowExplanation={shouldShowExplanation} />
                </AnnotatorCanvasSettingsProvider>
            </ProjectProvider>
        </ApplicationServicesProvider>,
        { services: { projectService: mockedProjectService } }
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return response;
};

const setQuickInference = (options: Partial<QuickInferenceContextProps>) => {
    jest.mocked(useQuickInference).mockReturnValue({
        isLoading: false,
        isDisabled: false,
        showWarningCard: false,
        explanation: undefined,
        explanations: [],
        annotations: [],
        image: undefined,
        predictionResult: undefined,
        setExplanation: jest.fn(),
        handleUploadImage: jest.fn(),
        showExplanation: false,
        setShowExplanation: jest.fn(),
        toggleShowPredictions: jest.fn(),
        showPredictions: false,
        imageWasUploaded: false,
        explanationOpacity: 1,
        setExplanationOpacity: jest.fn(),
        dismissWarningCard: jest.fn(),
        ...options,
    });
};

describe('SecondaryToolbar', () => {
    beforeEach(() => {
        setQuickInference({});
    });

    it('does not render explanation options', async () => {
        await renderApp({ shouldShowExplanation: false });

        expect(screen.queryByLabelText('opacity slider')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('explanation-switcher')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('show explanations dropdown')).not.toBeInTheDocument();
    });

    it('explanation switcher is enabled', async () => {
        setQuickInference({ isDisabled: false });

        await renderApp({});

        expect(screen.getByLabelText('explanation-switcher')).toBeEnabled();
    });

    it('isDisabled, disables explanation switcher', async () => {
        setQuickInference({ isDisabled: true });

        await renderApp({});

        expect(screen.getByLabelText('explanation-switcher')).toBeDisabled();
    });

    it('emptyLabel annotations disables explanation switcher', async () => {
        setQuickInference({ annotations: [emptyAnnotation] });

        await renderApp({});

        expect(screen.getByLabelText('explanation-switcher')).toBeDisabled();
    });

    it('selects explanation', async () => {
        const [label1, label2] = [
            getMockedLabel({ name: 'label-1', id: 'label-1' }),
            getMockedLabel({ name: 'label-2', id: 'label-2' }),
        ];

        const mockedSetExplanation = jest.fn();
        const explanationOne = getExplanation('123', label1.id);
        const explanationTwo = getExplanation('321', label2.id);

        setQuickInference({
            explanations: [explanationOne, explanationTwo],
            showExplanation: true,
            setExplanation: mockedSetExplanation,
        });

        await renderApp({ labels: [label1, label2] });

        fireEvent.click(screen.getByLabelText('show explanations dropdown'));

        await userEvent.selectOptions(screen.getByRole('listbox'), screen.getByRole('option', { name: label2.name }));

        expect(mockedSetExplanation).toHaveBeenCalledWith(explanationTwo);
    });
});
