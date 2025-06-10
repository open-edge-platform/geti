// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, fireEvent, screen, waitFor, waitForElementToBeRemoved, within } from '@testing-library/react';

import { createInMemoryInferenceService } from '../../../../../core/annotations/services/in-memory-inference-service';
import { createInMemoryModelsService } from '../../../../../core/models/services/in-memory-models-service';
import { DOMAIN, ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { ProjectService } from '../../../../../core/projects/services/project-service.interface';
import * as MediaValidators from '../../../../../providers/media-upload-provider/media-upload.validator';
import { mediaExtensionHandler } from '../../../../../providers/media-upload-provider/media-upload.validator';
import { VALID_IMAGE_TYPES } from '../../../../../shared/media-utils';
import { getMockedAnnotation } from '../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedModelsGroup } from '../../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getById } from '../../../../../test-utils/utils';
import { useDeviceSettings } from '../../../../camera-page/providers/device-settings-provider.component';
import { getUseCameraSettings } from '../../../../camera-page/test-utils/camera-setting';
import { UserCameraPermission } from '../../../../camera-support/camera.interface';
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

jest.mock('../../../../camera-page/providers/device-settings-provider.component', () => ({
    ...jest.requireActual('../../../../camera-page/providers/device-settings-provider.component'),
    useDeviceSettings: jest.fn(),
}));

jest.mock('../../../../../shared/navigator-utils', () => ({
    ...jest.requireActual('../../../../../shared/navigator-utils'),
    getVideoDevices: jest.fn().mockResolvedValue([]),
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

    const expectQuickInferenceIsReadyToUpload = async () => {
        expect(await screen.findByText('Drag and drop image')).toBeInTheDocument();
    };

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

        await expectQuickInferenceIsReadyToUpload();

        const file = new File(['hello'], 'hello.png', { type: 'image/png' });

        await uploadFile(screen.getByLabelText('upload link upload media input'), file);

        return { inferenceService, file };
    };

    it('upload button is disabled when no models trained', async () => {
        await renderQuickInference({ modelsGroup: [] });

        expect(screen.getByText('No trained models')).toBeInTheDocument();
        expect(screen.getByText('Upload media and annotate to test a model')).toBeInTheDocument();
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

        await expectQuickInferenceIsReadyToUpload();

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

        await expectQuickInferenceIsReadyToUpload();

        const filesWithUnsupportedFormats = [
            new File(['hello'], 'hello.mp4', { type: 'video/mp4' }),
            new File(['hello'], 'hello.txt', { type: 'text/txt' }),
        ];

        filesWithUnsupportedFormats.map(async (file) => {
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

    it('shows toggle buttons for "Use file" and "Use camera", "Use file" is selected by default', async () => {
        await renderQuickInference({});
        await expectQuickInferenceIsReadyToUpload();

        const useFileButton = screen.getByRole('button', { name: 'Use file' });
        const useCameraButton = screen.getByRole('button', { name: 'Use camera' });

        expect(useFileButton).toBeInTheDocument();
        expect(useCameraButton).toBeInTheDocument();

        expect(useFileButton).toHaveAttribute('data-activated', 'true');
        expect(useCameraButton).toHaveAttribute('data-activated', 'false');
    });

    describe('Live camera inference', () => {
        const clickUseCameraButton = () => {
            const useCameraButton = screen.getByRole('button', { name: 'Use camera' });
            fireEvent.click(useCameraButton);
            expect(useCameraButton).toHaveAttribute('data-activated', 'true');
        };

        it('shows loading when camera permission is not granted', async () => {
            jest.mocked(useDeviceSettings).mockReturnValue(
                getUseCameraSettings({
                    userPermissions: UserCameraPermission.PENDING,
                })
            );

            await renderQuickInference({});
            await expectQuickInferenceIsReadyToUpload();

            clickUseCameraButton();

            expect(screen.getByLabelText('permissions pending')).toBeInTheDocument();
        });

        it('shows an error message when there is an error with camera', async () => {
            jest.mocked(useDeviceSettings).mockReturnValue(
                getUseCameraSettings({
                    userPermissions: UserCameraPermission.ERRORED,
                })
            );

            await renderQuickInference({});
            await expectQuickInferenceIsReadyToUpload();

            clickUseCameraButton();

            expect(
                screen.getAllByText('Please check your device and network settings and try again.')[0]
            ).toBeInTheDocument();
        });

        it('shows camera view with settings', async () => {
            jest.mocked(useDeviceSettings).mockReturnValue(
                getUseCameraSettings({
                    deviceConfig: [
                        {
                            name: 'frameRate',
                            config: {
                                type: 'minMax',
                                value: 30,
                                max: 30,
                                min: 0,
                            },
                            onChange: jest.fn(),
                        },
                        {
                            name: 'height',
                            config: {
                                type: 'minMax',
                                value: 480,
                                max: 1920,
                                min: 1,
                            },
                            onChange: jest.fn(),
                        },
                        {
                            name: 'resizeMode',
                            config: {
                                type: 'selection',
                                value: 'none',
                                options: ['none', 'crop-and-scale'],
                            },
                            onChange: jest.fn(),
                        },
                        {
                            name: 'width',
                            config: {
                                type: 'minMax',
                                value: 640,
                                max: 1920,
                                min: 1,
                            },
                            onChange: jest.fn(),
                        },
                    ],
                    userPermissions: UserCameraPermission.GRANTED,
                })
            );

            await renderQuickInference({});
            await expectQuickInferenceIsReadyToUpload();

            clickUseCameraButton();
            expect(screen.getByRole('heading', { name: 'Camera Settings' })).toBeInTheDocument();
        });
    });
});
