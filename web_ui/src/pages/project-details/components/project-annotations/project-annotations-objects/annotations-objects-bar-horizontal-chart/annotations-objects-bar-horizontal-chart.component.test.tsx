import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { ResponsiveContainer } from 'recharts';

import { createInMemoryProjectService } from '../../../../../../core/projects/services/in-memory-project-service';
import { getMockedLabel } from '../../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../../../test-utils/mocked-items-factory/mocked-project';
import { projectRender as render } from '../../../../../../test-utils/project-provider-render';
import { AnnotationObjectsBarHorizontalChart } from './annotations-objects-bar-horizontal-chart.component';

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(() => mockedNavigate),
}));

const mockedDatasetIdentifier = {
    workspaceId: 'test-workspace',
    projectId: 'test-project',
    datasetId: 'test-dataset',
};
jest.mock('../../../../../annotator/hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: jest.fn(() => mockedDatasetIdentifier),
}));

describe('AnnotationsObjectsBarHorizontalChart', () => {
    const data = [
        { name: 'Car', value: 5 },
        { name: 'Bike', value: 3 },
    ];

    const renderApp = async () => {
        const projectService = createInMemoryProjectService();
        const mockedColors = [
            { color: '#FF0000', fadedColor: '#FF0000' },
            { color: '#000000', fadedColor: '#000000' },
        ];
        const mockProject = getMockedProject({
            labels: [
                getMockedLabel({
                    id: 'label-1',
                    name: 'Car',
                }),
                getMockedLabel({
                    id: 'label-2',
                    name: 'Bike',
                }),
            ],
        });
        projectService.getProject = async () => mockProject;

        render(
            <ResponsiveContainer>
                <AnnotationObjectsBarHorizontalChart title='Objects Chart' data={data} colors={mockedColors} />
            </ResponsiveContainer>,
            {
                services: { projectService },
            }
        );
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('calls handleLabelClick with correct label when bar is clicked', async () => {
        const handleLabelClick = jest.fn();

        await renderApp();

        fireEvent.click(screen.getByLabelText('Car'));

        expect(handleLabelClick).toHaveBeenCalledWith('Car');
        expect(mockedNavigate).toHaveBeenCalled();
    });
});
