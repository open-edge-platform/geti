// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import capitalize from 'lodash/capitalize';

import { useProjectActions } from '../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectSortingOptions } from '../../../../../core/projects/services/project-service.interface';
import { KeypointTask } from '../../../../../core/projects/task.interface';
import { isKeypointTask } from '../../../../../core/projects/utils';
import { useWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { hasEqualId } from '../../../../../shared/utils';
import { RawTemplate } from '../templates/utils';

export const useGetProjectsTemplates = () => {
    const { useGetProjects } = useProjectActions();
    const { organizationId, workspaceId } = useWorkspaceIdentifier();

    const projectsQuery = useGetProjects(
        { organizationId, workspaceId },
        { sortBy: ProjectSortingOptions.creationDate, sortDir: 'dsc' }
    );

    const pages = projectsQuery.data?.pages ?? [];
    const keypointProjects = pages
        .flatMap(({ projects }) => projects)
        .filter(({ tasks }) => tasks.some(isKeypointTask));

    return keypointProjects.map((project): RawTemplate => {
        const keypointTask = project.tasks[0] as KeypointTask;

        return {
            name: capitalize(project.name),
            template: {
                // Convert labels to use names instead of IDs since we don't have IDs when creating a new project
                edges: keypointTask.keypointStructure.edges.map(({ nodes }) => ({
                    from: project.labels.find(hasEqualId(nodes[0]))?.name ?? '',
                    to: project.labels.find(hasEqualId(nodes[1]))?.name ?? '',
                })),
                points: keypointTask.keypointStructure.positions.map(({ x, y, label }) => ({
                    x,
                    y,
                    label: label.name,
                })),
            },
        };
    });
};
