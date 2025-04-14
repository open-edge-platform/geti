// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { SearchRuleField } from '../../../../core/media/media-filter.interface';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { MediaFilterValueFactory } from './media-filter-value-factory';

jest.mock('../../../../providers/workspaces-provider/workspaces-provider.component', () => ({
    useWorkspaces: jest.fn(() => ({ workspaceId: 'testing-workspace' })),
}));

jest.mock('../../providers/media-provider.component', () => ({
    useMedia: jest.fn(() => ({
        anomalyLabel: undefined,
    })),
}));

const mockLabels = [
    { name: 'test 1', id: '2020' },
    { name: 'test2', id: '2021' },
    { name: 'test3', id: '2022' },
];
const tasks = [getMockedTask({ labels: mockLabels.map(({ id, name }) => getMockedLabel({ name, id })) })];

const mockProject = getMockedProject({
    tasks,
});

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    useProject: () => ({ project: mockProject }),
}));

describe('MediaFilterValueFactory', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const renderApp = (field: SearchRuleField | '') => {
        const onSelectionChange = jest.fn();
        render(
            <MediaFilterValueFactory
                value=''
                field={field}
                isAnomalyProject={false}
                onSelectionChange={onSelectionChange}
            />
        );
        return { onSelectionChange };
    };

    it('shape area percentage', () => {
        renderApp(SearchRuleField.ShapeAreaPercentage);

        expect(screen.queryByLabelText('media-filter-shape-area-percentage')).toBeInTheDocument();
    });

    it('shape type', () => {
        renderApp(SearchRuleField.ShapeType);

        expect(screen.queryByLabelText('media-filter-shape-type')).toBeInTheDocument();
    });

    it('Media upload date', () => {
        renderApp(SearchRuleField.MediaUploadDate);

        expect(screen.queryByLabelText('media filter date')).toBeInTheDocument();
    });

    it('Annotation creation date', () => {
        renderApp(SearchRuleField.AnnotationCreationDate);

        expect(screen.queryByLabelText('media filter date')).toBeInTheDocument();
    });

    it('Annotation scene state', () => {
        renderApp(SearchRuleField.AnnotationSceneState);

        expect(screen.queryByLabelText('media-filter-annotation-scene-state')).toBeInTheDocument();
    });

    it('Label', () => {
        renderApp(SearchRuleField.LabelId);

        expect(screen.queryByLabelText('media-filter-label')).toBeInTheDocument();
    });

    it('Media width', () => {
        renderApp(SearchRuleField.MediaWidth);

        expect(screen.queryByLabelText('Media filter size')).toBeInTheDocument();
    });

    it('Media height', () => {
        renderApp(SearchRuleField.MediaHeight);

        expect(screen.queryByLabelText('Media filter size')).toBeInTheDocument();
    });

    it('user name', () => {
        renderApp(SearchRuleField.UserName);

        expect(screen.queryByLabelText('media-filter-users-list')).toBeInTheDocument();
    });

    it('default field', () => {
        renderApp('');
        expect(screen.queryByLabelText('media-filter-name')).toBeInTheDocument();
    });
});
