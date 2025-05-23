import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../../../../test-utils/required-providers-render';
import { TrainingModelCard } from './training-model-card.component';

const mockJob = {
    metadata: {
        task: {
            modelArchitecture: 'ResNet',
        },
        trainedModel: {
            modelId: '123',
        },
    },
    creationTime: '2024-05-21T12:00:00Z',
};

jest.mock('../../../../../../core/models/hooks/use-models.hook', () => ({
    useModels: () => ({
        useProjectModelsQuery: () => ({
            data: [
                {
                    modelVersions: [{ groupName: 'ResNet', version: 1 }],
                },
            ],
        }),
    }),
}));

jest.mock('../model-card/model-performance.component', () => ({
    ModelPerformance: () => <div data-testid='model-performance' />,
}));

jest.mock('../model-card/model-info-fields.component', () => ({
    ModelInfoFields: (props: any) => <div data-testid='model-info-fields'>{JSON.stringify(props)}</div>,
}));

describe('TrainingModelCard', () => {
    it('renders with correct version and architecture', () => {
        render(<TrainingModelCard job={mockJob as any} />);
        expect(screen.getByLabelText(/ResNet version 2/i)).toBeInTheDocument();
        expect(screen.getByTestId('version-training-model-123-id')).toHaveTextContent('Version 2');
    });

    it('renders trained date', () => {
        render(<TrainingModelCard job={mockJob as any} />);
        expect(screen.getByTestId('trained-model-date-id')).toHaveTextContent('Trained: 21 May 2024, 12:00 PM');
    });

    it('renders ModelPerformance and ModelInfoFields', () => {
        render(<TrainingModelCard job={mockJob as any} />);
        expect(screen.getByTestId('model-performance')).toBeInTheDocument();
        expect(screen.getByTestId('model-info-fields')).toBeInTheDocument();
    });
});
