// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { VALID_IMAGE_TYPES } from '@shared/media-utils';
import { act, fireEvent, screen, waitFor, waitForElementToBeRemoved, within } from '@testing-library/react';

import { createInMemoryInferenceService } from '../../../../../core/annotations/services/in-memory-inference-service';
import { createInMemoryModelsService } from '../../../../../core/models/services/in-memory-models-service';
import { DOMAIN, ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../../core/projects/services/project-service.interface';
import * as MediaValidators from '../../../../../providers/media-upload-provider/media-upload.validator';
import { mediaExtensionHandler } from '../../../../../providers/media-upload-provider/media-upload.validator';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedModelsGroup } from '../../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getById } from '../../../../../test-utils/utils';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { QuickInference } from './quick-inference.component';

jest.setTimeout(10000);

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-123',
        workspaceId: 'workspace_1',
        organizationId: 'organization-id',
    }),
}));

describe('QuickInference', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    beforeAll(() => {
        jest.spyOn(MediaValidators, 'validateMedia').mockImplementation((file) => Promise.resolve(file));

        jest.spyOn(global, 'FileReader').mockImplementation(function () {
            // @ts-expect-error We dont care about typing "this"
            this.readAsDataURL = jest.fn();

            // @ts-expect-error We dont care about typing "this"
            this.onload = jest.fn();

            // @ts-expect-error We dont care about typing "this"
            return this;
        });
    });

    const renderQuickInference = async ({
        modelsGroup,
        projectService = createInMemoryProjectService(),
        projectIdentifier = getMockedProjectIdentifier({}),
    }: {
        modelsGroup?: [];
        projectService?: ProjectService;
        projectIdentifier?: ProjectIdentifier;
    }) => {
        const inferenceService = createInMemoryInferenceService();
        const modelsService = createInMemoryModelsService();

        modelsService.getModels = jest.fn(async () => modelsGroup ?? [getMockedModelsGroup()]);

        inferenceService.getPredictionsForFile = jest.fn(async () => {
            return [];
        });

        const { container } = render(
            <ProjectProvider projectIdentifier={projectIdentifier}>
                <QuickInference />
            </ProjectProvider>,
            {
                services: { projectService, inferenceService, modelsService },
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        const inputElement = getById(container, 'upload-media-button-id-input-file') as HTMLElement;

        modelsGroup?.length &&
            (await waitFor(() => {
                expect(inputElement).toBeEnabled();
            }));

        return { inferenceService, container };
    };

    const uploadFile = async (element: HTMLElement, file: File) => {
        fireEvent.change(element, { target: { files: [file] } });

        // This line tells jest to "wait a bit" before the execution of the next line.
        // It's a way to flush promises in the scenario where we have async calls inside a method
        await Promise.resolve();

        // @ts-expect-error This is mocked
        const reader = FileReader.mock.instances[0];

        if (reader) {
            await act(() => reader.onload({ target: { result: file } }));
        }
    };

    const renderAndUploadFile = async (
        projectService = createInMemoryProjectService(),
        projectIdentifier = getMockedProjectIdentifier()
    ) => {
        const { inferenceService } = await renderQuickInference({ projectService, projectIdentifier });

        inferenceService.getPredictionsForFile = jest.fn(async () => {
            return [getMockedAnnotation({ id: 'annotation-1' }), getMockedAnnotation({ id: 'annotation-2' })];
        });
        inferenceService.getExplanationsForFile = jest.fn(async () => {
            return [];
        });

        const file = new File(['hello'], 'hello.png', { type: 'image/png' });

        await uploadFile(screen.getByLabelText('upload link upload media input'), file);

        return { inferenceService, file };
    };

    it('upload button is disabled when no models trained', async () => {
        await renderQuickInference({ modelsGroup: [] });

        const inputElement = screen.getByText('Upload media');
        expect(inputElement).toBeEnabled();
    });

    it('should has drag and drop image text', async () => {
        await renderQuickInference({});

        expect(await screen.findByText('Drag and drop image')).toBeInTheDocument();
    });

    it('uploads an image and gets inference for it', async () => {
        const project = getMockedProject({ id: 'project-123' });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => project;

        const projectIdentifier = getMockedProjectIdentifier({
            projectId: project.id,
            workspaceId: 'workspace_1',
            organizationId: 'organization-id',
        });

        const { inferenceService, file } = await renderAndUploadFile(projectService);

        expect(await screen.findByLabelText('annotations')).toBeInTheDocument();

        expect(inferenceService.getPredictionsForFile).toHaveBeenCalledWith(projectIdentifier, project.labels, file);
    });

    it('shows an error message when prediction fails', async () => {
        const { inferenceService, container } = await renderQuickInference({});
        inferenceService.getPredictionsForFile = jest.fn(() => {
            throw new Error('Some 503 error from the server');
        });

        const file = new File(['hello'], 'hello.png', { type: 'image/png' });
        const inputElement = getById(container, 'upload-media-button-id-input-file') as HTMLElement;

        await uploadFile(inputElement, file);

        // Inference has failed so we should see an alert and a loading indicator,
        // while it is retrying
        expect(await screen.findByRole('alert')).toBeInTheDocument();

        // Main loading plus the inference small loading
        expect(screen.getAllByRole('progressbar')).toHaveLength(2);

        expect(screen.getByLabelText('annotations')).toBeInTheDocument();
    });

    it('uploads an image and gets inference for it in fullscreen', async () => {
        const project = getMockedProject({ id: 'project-123' });
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => project;

        const projectIdentifier = getMockedProjectIdentifier({
            projectId: project.id,
            workspaceId: 'workspace_1',
            organizationId: 'organization-id',
        });

        const { inferenceService, file } = await renderAndUploadFile(projectService, projectIdentifier);

        fireEvent.click(screen.getByRole('button', { name: /Open in fullscreen/ }));

        const dialog = screen.getByRole('dialog');

        expect(await within(dialog).findByLabelText('annotations')).toBeInTheDocument();

        expect(inferenceService.getPredictionsForFile).toHaveBeenCalledWith(projectIdentifier, project.labels, file);

        fireEvent.click(screen.getByRole('button', { name: 'Close fullscreen' }));

        await waitForElementToBeRemoved(dialog);
    });

    it('shows error notification if the user tries to upload a non-image file', async () => {
        const { inferenceService } = await renderQuickInference({});

        const filesWithUnsupportedFormats = [
            new File(['hello'], 'hello.mp4', { type: 'video/mp4' }),
            new File(['hello'], 'hello.txt', { type: 'text/txt' }),
        ];

        filesWithUnsupportedFormats.forEach(async (file) => {
            await uploadFile(screen.getByLabelText('upload link upload media input'), file);

            await Promise.resolve();

            expect(
                screen.getByText(
                    `This feature only supports image files. Supported extensions: ${mediaExtensionHandler(
                        VALID_IMAGE_TYPES
                    )}`
                )
            ).toBeInTheDocument();

            expect(inferenceService.getPredictionsForFile).not.toHaveBeenCalled();
        });

        expect(await screen.findByRole('button', { name: 'close notification' })).toBeInTheDocument();
        expect(screen.getByText('This feature only supports image files.', { exact: false })).toBeInTheDocument();
    });

    it('Hide predictions and canvas adjustments buttons are not visible when image was not uploaded', async () => {
        await renderQuickInference({});

        expect(screen.queryByRole('button', { name: /hide predictions/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /canvas adjustments/i })).not.toBeInTheDocument();
    });

    it('Upload in the header, hide predictions and canvas adjustments buttons are visible when image is uploaded', async () => {
        await renderAndUploadFile();

        expect(screen.getByRole('button', { name: /hide predictions/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /canvas adjustments/i })).toBeInTheDocument();
    });

    it('Upload in the header, hide predictions and canvas adjustments buttons are visible when image is uploaded - full screen mode', async () => {
        await renderAndUploadFile();

        fireEvent.click(screen.getByRole('button', { name: /Open in fullscreen/i }));

        expect(screen.getByRole('button', { name: /upload file/i })).toBeVisible();
        expect(screen.getByRole('button', { name: /hide predictions/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /canvas adjustments/i })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Close fullscreen' }));
    });

    it('Predictions should be hidden', async () => {
        await renderAndUploadFile();

        await waitFor(() => {
            expect(screen.getByLabelText('annotations-canvas-annotation-1-shape')).toBeInTheDocument();
            expect(screen.getByLabelText('annotations-canvas-annotation-2-shape')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /hide predictions/i }));

        expect(screen.queryByLabelText('annotations-canvas-annotation-1-shape')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('annotations-canvas-annotation-2-shape')).not.toBeInTheDocument();
    });

    // TODO: Once we implement per-task explanation maps for live prediction feature
    it('does not render explanation options on the secondary bar if the project is task chain', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () =>
            getMockedProject({ domains: [DOMAIN.DETECTION, DOMAIN.CLASSIFICATION] });

        await renderQuickInference({ projectService });

        expect(screen.queryByLabelText('opacity slider')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('explanation-switcher')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('show explanations dropdown')).not.toBeInTheDocument();
    });

    it('does not render explanation options on the secondary bar if the project is keypoint', async () => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () =>
            getMockedProject({
                domains: [DOMAIN.KEYPOINT_DETECTION],
                tasks: [getMockedTask({ id: 'task_c', domain: DOMAIN.KEYPOINT_DETECTION })],
            });

        await renderAndUploadFile(projectService);

        expect(screen.queryByLabelText('opacity slider')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('explanation-switcher')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('show explanations dropdown')).not.toBeInTheDocument();
    });
});
