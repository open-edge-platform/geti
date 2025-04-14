// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { ModelsGroups } from '../../../../../core/models/models.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedModelsGroup } from '../../../../../test-utils/mocked-items-factory/mocked-model';
import { getMockedProject } from '../../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender } from '../../../../../test-utils/required-providers-render';
import { PreselectedModel } from '../../../project-details.interface';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { RunTestDialogContent } from './run-test-dialog-content.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        projectId: 'project-id',
        workspaceId: 'workspace-id',
        organizationId: 'organization-id',
    }),
}));

const mockedDetectionTask = getMockedTask({ id: 'detection-task-id', domain: DOMAIN.DETECTION });
const mockedSegmentationTask = getMockedTask({ id: 'segmentation-task-id', domain: DOMAIN.SEGMENTATION });
const mockSegmentationProject = getMockedProject({
    name: 'In memory segmentation',
    domains: [DOMAIN.SEGMENTATION],
    tasks: [mockedSegmentationTask],
});

const mockedModelsGroup = getMockedModelsGroup({
    groupId: 'group-1-id',
    groupName: 'group-1',
    taskId: mockedSegmentationTask.id,
    modelTemplateName: 'Accuracy',
});
const mockedModelsGroupTwo = getMockedModelsGroup({
    groupId: 'group-2-id',
    groupName: 'group-2',
    taskId: mockedSegmentationTask.id,
});

const mockedModelsGroupDetection = getMockedModelsGroup({
    groupId: 'group-3-id',
    groupName: 'group-3',
    taskId: mockedDetectionTask.id,
});

const mockedPreselectedModel: PreselectedModel = {
    ...mockedModelsGroup,
    version: mockedModelsGroup.modelVersions[0].version,
    id: mockedModelsGroup.groupId,
    templateName: mockedModelsGroup.modelTemplateName,
};

const renderApp = async ({
    project = mockSegmentationProject,
    modelsGroups,
    preselectedModel,
}: {
    project?: ProjectProps;
    modelsGroups: ModelsGroups[];
    preselectedModel?: PreselectedModel;
}) => {
    const projectService = createInMemoryProjectService();
    projectService.getProject = async () => project;

    providersRender(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
            <RunTestDialogContent
                handleClose={jest.fn()}
                modelsGroups={modelsGroups}
                preselectedModel={preselectedModel}
            />
        </ProjectProvider>,
        { services: { projectService } }
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
};

const getPreselectedModelInfoSelector = ({
    domain,
    version,
    templateName,
    groupName,
}: {
    domain: DOMAIN;
    version: number;
    templateName: string;
    groupName: string;
}) => ({
    domain: screen.queryByText(domain),
    version: screen.queryByTestId(`version-${version}-id`),
    templateNameAndGroup: screen.queryByTestId(new RegExp(`${templateName}.*\\(${groupName}\\).*id`, 'i')),
});

describe('RunTestDialogContent', () => {
    const taskChainProject = getMockedProject({
        name: 'In memory segmentation',
        domains: [DOMAIN.SEGMENTATION],
        tasks: [mockedDetectionTask, mockedSegmentationTask],
    });

    describe('task chain project', () => {
        it('renders PreselectedModelInfo if a model is preselected', async () => {
            await renderApp({ project: taskChainProject, modelsGroups: [], preselectedModel: mockedPreselectedModel });

            const preselectedModelInfoSelector = getPreselectedModelInfoSelector({
                ...mockedPreselectedModel,
                domain: mockedSegmentationTask.domain,
                version: mockedPreselectedModel.version,
            });

            expect(screen.queryByRole('button', { name: /Select task type/i })).not.toBeInTheDocument();
            expect(screen.queryByRole('button', { name: /Select model/i })).not.toBeInTheDocument();
            expect(screen.queryByRole('button', { name: /Select version/i })).not.toBeInTheDocument();

            expect(preselectedModelInfoSelector.domain).toBeVisible();
            expect(preselectedModelInfoSelector.version).toBeVisible();
            expect(preselectedModelInfoSelector.templateNameAndGroup).toBeVisible();
        });

        it('model and version are preselected by default', async () => {
            await renderApp({
                project: taskChainProject,
                modelsGroups: [mockedModelsGroupDetection],
            });

            const preselectedModelInfoSelector = getPreselectedModelInfoSelector({
                ...mockedPreselectedModel,
                domain: mockedSegmentationTask.domain,
                version: mockedPreselectedModel.version,
            });

            expect(preselectedModelInfoSelector.version).not.toBeInTheDocument();
            expect(preselectedModelInfoSelector.templateNameAndGroup).not.toBeInTheDocument();

            expect(screen.getByLabelText(/Select task type/i)).toHaveTextContent('Detection');
            expect(
                screen.getByRole('button', {
                    name: `Version ${mockedModelsGroupDetection.modelVersions[0].version} Version`,
                })
            ).toBeVisible();

            expect(
                screen.getByRole('button', {
                    name: `${mockedModelsGroupDetection.groupName} (${mockedModelsGroupDetection.modelVersions[0].templateName}) Model`,
                })
            ).toBeVisible();
        });
    });

    describe('single project', () => {
        it('renders PreselectedModelInfo if a model is preselected', async () => {
            await renderApp({ modelsGroups: [], preselectedModel: mockedPreselectedModel });

            const preselectedModelInfoSelector = getPreselectedModelInfoSelector({
                ...mockedPreselectedModel,
                domain: mockedSegmentationTask.domain,
                version: mockedPreselectedModel.version,
            });

            expect(screen.queryByRole('button', { name: /Select task type/i })).not.toBeInTheDocument();
            expect(screen.queryByRole('button', { name: /Select model/i })).not.toBeInTheDocument();
            expect(screen.queryByRole('button', { name: /Select version/i })).not.toBeInTheDocument();

            expect(preselectedModelInfoSelector.domain).toBeVisible();
            expect(preselectedModelInfoSelector.version).toBeVisible();
            expect(preselectedModelInfoSelector.templateNameAndGroup).toBeVisible();
        });

        it('model and version are preselected by default', async () => {
            await renderApp({
                modelsGroups: [mockedModelsGroup, mockedModelsGroupTwo],
            });

            const preselectedModelInfoSelector = getPreselectedModelInfoSelector({
                domain: mockedSegmentationTask.domain,
                version: mockedModelsGroup.modelVersions[0].version,
                templateName: mockedModelsGroup.modelTemplateId,
                groupName: mockedModelsGroup.groupName,
            });

            expect(preselectedModelInfoSelector.domain).not.toBeInTheDocument();
            expect(preselectedModelInfoSelector.version).not.toBeInTheDocument();
            expect(preselectedModelInfoSelector.templateNameAndGroup).not.toBeInTheDocument();
            expect(screen.queryByRole('button', { name: /Select model/i })).not.toBeInTheDocument();
            expect(screen.queryByRole('button', { name: /Select version/i })).not.toBeInTheDocument();

            expect(
                screen.getByRole('button', { name: `Version ${mockedPreselectedModel.version} Version` })
            ).toBeVisible();

            expect(
                screen.getByRole('button', {
                    name: `${mockedPreselectedModel.groupName} (${mockedPreselectedModel.templateName}) Model`,
                })
            ).toBeVisible();
        });
    });
});
