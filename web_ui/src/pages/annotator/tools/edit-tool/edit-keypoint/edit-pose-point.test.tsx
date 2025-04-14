// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { createInMemoryUserSettingsService } from '../../../../../core/user-settings/services/in-memory-user-settings-service';
import { UserSettingsService } from '../../../../../core/user-settings/services/user-settings.interface';
import { getMockedDatasetIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { projectRender } from '../../../../../test-utils/project-provider-render';
import { AnnotatorContextMenuProvider } from '../../../providers/annotator-context-menu-provider/annotator-context-menu-provider.component';
import { AnnotatorProviders } from '../../../test-utils/annotator-render';
import { TransformZoomAnnotation } from '../../../zoom/transform-zoom-annotation.component';
import { ZoomProvider } from '../../../zoom/zoom-provider.component';
import { EditPosePoint } from './edit-pose-point.component';

const mockedLabel = getMockedLabel({ name: 'point-name' });

describe('EditPosePoint', () => {
    const renderApp = async ({
        isLabelVisible = false,
        point = getMockedKeypointNode({}),
        onToggleVisibility = jest.fn(),
        userSettingsService = createInMemoryUserSettingsService(),
    }: {
        point?: KeypointNode;
        isLabelVisible?: boolean;
        userSettingsService?: UserSettingsService;
        onToggleVisibility?: () => void;
    }) => {
        projectRender(
            <AnnotatorProviders datasetIdentifier={getMockedDatasetIdentifier()}>
                <ZoomProvider>
                    <TransformZoomAnnotation>
                        <AnnotatorContextMenuProvider>
                            <svg>
                                <EditPosePoint
                                    isLabelVisible={isLabelVisible}
                                    roi={{ x: 1, y: 1, width: 1, height: 1 }}
                                    point={point}
                                    onComplete={jest.fn()}
                                    moveAnchorTo={jest.fn()}
                                    onToggleVisibility={onToggleVisibility}
                                />
                            </svg>
                        </AnnotatorContextMenuProvider>
                    </TransformZoomAnnotation>
                </ZoomProvider>
            </AnnotatorProviders>,
            {
                services: { userSettingsService },
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    describe('Pose point label', () => {
        it('pose label should be hidden when canvasSettings.hideLabels is true', async () => {
            const userSettingsService = createInMemoryUserSettingsService();
            const settings = await userSettingsService.getProjectSettings(getMockedDatasetIdentifier());

            userSettingsService.getProjectSettings = async () => {
                return { ...settings, hideLabels: { value: true, defaultValue: false } };
            };

            await renderApp({
                point: getMockedKeypointNode({ label: mockedLabel }),
                isLabelVisible: true,
                userSettingsService,
            });

            expect(screen.queryByLabelText(`pose label ${mockedLabel.name}`)).not.toBeInTheDocument();
        });
    });
    it('occlude the point when the context menu option is selected', async () => {
        const optionText = 'Mark as occluded';
        const mockedOnToggleVisibility = jest.fn();
        const mockedKeypointNode = getMockedKeypointNode({ label: mockedLabel });

        await renderApp({ point: mockedKeypointNode, onToggleVisibility: mockedOnToggleVisibility });

        const point = screen.getByLabelText(`Resize keypoint ${mockedLabel.name} anchor`);
        fireEvent.contextMenu(point);

        fireEvent.click(screen.getByRole('menuitem', { name: new RegExp(optionText, 'i') }));

        expect(mockedOnToggleVisibility).toHaveBeenLastCalledWith(optionText);
    });

    it('display the point when the context menu option is selected', async () => {
        const optionText = 'Mark as visible';
        const mockedOnToggleVisibility = jest.fn();
        const mockedKeypointNode = getMockedKeypointNode({ label: mockedLabel, isVisible: false });

        await renderApp({ point: mockedKeypointNode, onToggleVisibility: mockedOnToggleVisibility });

        const point = screen.getByLabelText(`Resize keypoint ${mockedLabel.name} anchor`);
        fireEvent.contextMenu(point);

        fireEvent.click(screen.getByRole('menuitem', { name: new RegExp(optionText, 'i') }));

        expect(mockedOnToggleVisibility).toHaveBeenLastCalledWith(optionText);
    });
});
