// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useNavigate } from 'react-router-dom';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { ApplicationServicesContextProps } from '../../../../core/services/application-services-provider.component';
import { useHistoryBlock } from '../../../../hooks/use-history-block/use-history-block.hook';
import { applicationRender as render } from '../../../../test-utils/application-provider-render';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { checkTooltip } from '../../../../test-utils/utils';
import { ProjectProvider } from '../../providers/project-provider/project-provider.component';
import { ProjectLabels } from './project-labels.component';

jest.mock('../../../../hooks/use-history-block/use-history-block.hook', () => ({
    ...jest.requireActual('../../../../hooks/use-history-block/use-history-block.hook'),
    useHistoryBlock: jest.fn(),
}));

const App = ({ projectId }: { projectId: string }): JSX.Element => {
    const navigate = useNavigate();
    const mockedProjectIdentifier = getMockedProjectIdentifier({ projectId, workspaceId: 'default' });

    return (
        <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
            <>
                <button onClick={() => navigate('/')}>Go home</button>
                <ProjectLabels />
            </>
        </ProjectProvider>
    );
};

const renderApp = async ({
    projectId,
    services,
}: {
    projectId: string;
    services?: Partial<ApplicationServicesContextProps>;
}) => {
    await render(<App projectId={projectId} />, { services });

    fireEvent.click(await screen.findByRole('button', { name: /edit labels/i }));
};

const parentId = 'first-task-label-id';
const detectionClassificationMockedProject = {
    id: 'test-detection-classification',
    tasks: [
        getMockedTask({
            id: 'task-1',
            domain: DOMAIN.DETECTION,
            title: 'Detection',
            labels: [
                getMockedLabel({
                    parentLabelId: null,
                    group: 'Default group root task',
                    name: 'pets',
                    id: parentId,
                }),
            ],
        }),
        getMockedTask({
            id: 'task-2',
            domain: DOMAIN.CLASSIFICATION,
            title: 'Classification',
            labels: [
                getMockedLabel({
                    parentLabelId: parentId,
                    group: 'Default group root task___pets group',
                    name: 'cat',
                    id: 'cat-id',
                }),
                getMockedLabel({
                    parentLabelId: parentId,
                    group: 'Default group root task___pets group',
                    name: 'dog',
                    id: 'dog-id',
                }),
                getMockedLabel({
                    parentLabelId: 'dog-id',
                    group: 'house-animals',
                    name: 'cocker',
                    id: 'cocker-id',
                }),
            ],
        }),
    ],
};
describe('Project labels', () => {
    const mockDefaultUseHistoryBlock = () => {
        // This mock makes it so that the history block isn't activated
        jest.mocked(useHistoryBlock).mockImplementation(() => {
            return [false, jest.fn(), jest.fn()];
        });
    };

    beforeAll(() => {
        mockDefaultUseHistoryBlock();
    });

    afterAll(() => {
        jest.resetAllMocks();
    });

    describe(`Segmentation`, () => {
        const addLabel = (name: string) => {
            fireEvent.input(screen.getByRole('textbox', { name: 'Project label name input' }), {
                target: { value: name },
            });
            fireEvent.click(screen.getByRole('button', { name: 'Create label' }));
        };

        it('Should open saving popup when there are some new labels', async () => {
            await renderApp({ projectId: 'test' });

            addLabel('test');
            fireEvent.click(screen.getByRole('button', { name: 'Save' }));
            expect(screen.getByRole('button', { name: 'Assign' })).toBeInTheDocument();
        });

        it('Should not open saving popup when there are only idle, edited or deleted labels', async () => {
            await renderApp({ projectId: 'test' });

            fireEvent.click(screen.getByRole('button', { name: 'delete' }));
            fireEvent.click(screen.getByRole('button', { name: 'Save' }));

            expect(screen.queryByRole('button', { name: 'Assign' })).not.toBeInTheDocument();

            await waitFor(() => {
                expect(screen.getByText('Labels have been changed successfully.')).toBeInTheDocument();
            });
        });

        it('Saving with shouldRevisit flag - text "Labels have been changed successfully. All affected images are assigned the Revisit status." is in notification', async () => {
            await renderApp({ projectId: 'test' });

            addLabel('test2');
            fireEvent.click(screen.getByRole('button', { name: 'Save' }));
            fireEvent.click(screen.getByRole('button', { name: 'Assign' }));

            await waitFor(() => {
                expect(
                    screen.getByText(
                        'Labels have been changed successfully. All affected images are assigned the Revisit status.'
                    )
                ).toBeInTheDocument();
            });
        });

        it('Saving without shouldRevisit flag - text "Labels have been changed successfully." is in notification', async () => {
            await renderApp({ projectId: 'test' });

            addLabel('test2');
            fireEvent.click(screen.getByRole('button', { name: 'Save' }));
            fireEvent.click(screen.getByRole('button', { name: "Don't assign" }));

            await waitFor(() => {
                expect(screen.getByText('Labels have been changed successfully.')).toBeInTheDocument();
            });
        });

        it('Saving deleted labels - text "Labels have been changed successfully." is in notification', async () => {
            await renderApp({ projectId: 'test' });

            fireEvent.click(screen.getByRole('button', { name: 'delete' }));
            fireEvent.click(screen.getByRole('button', { name: 'Save' }));

            await waitFor(() => {
                expect(screen.getByText('Labels have been changed successfully.')).toBeInTheDocument();
            });
        });

        it('Should show unsaved changes dialog when user tries to change url while editing labels', async () => {
            jest.mocked(useHistoryBlock).mockImplementation(() => [true, jest.fn(), jest.fn()]);

            await render(<App projectId={'test'} />);

            expect(screen.getByRole('alertdialog')).toBeInTheDocument();
            fireEvent.click(screen.getByRole('button', { name: 'Stay on page' }));
            mockDefaultUseHistoryBlock();
        });
    });

    describe('Classification', () => {
        it('Check multi/single selection tooltips', async () => {
            await renderApp({ projectId: 'test-classification' });

            await checkTooltip(
                screen.getAllByText('Single selection')[0],
                'Only one label from such group can be applied to an image/frame.'
            );
        });
    });

    describe('Detection -> Classification', () => {
        const projectService = createInMemoryProjectService();
        const getCreateChildButtonId = (name: string, type: 'group' | 'label') =>
            `${name}-label-add-child-${type}-button`;

        projectService.getProject = async () => getMockedProject(detectionClassificationMockedProject);

        it('cannot add group to default root group', async () => {
            await renderApp({
                projectId: 'test-detection-classification',
                services: { projectService },
            });

            expect(screen.queryByTestId('Default group root task-add-child-group-button')).not.toBeInTheDocument();
        });

        it('can add a group to a non-group label', async () => {
            await renderApp({
                projectId: 'test-detection-classification',
                services: { projectService },
            });

            expect(screen.getByTestId(getCreateChildButtonId('cat', 'group'))).toBeInTheDocument();
            expect(screen.getByTestId(getCreateChildButtonId('dog', 'group'))).toBeInTheDocument();
        });

        it('can add a label to group labels (non-root)', async () => {
            await renderApp({
                projectId: 'test-detection-classification',
                services: { projectService },
            });

            expect(screen.getByTestId(getCreateChildButtonId('cocker', 'group'))).toBeInTheDocument();
        });
    });
});
