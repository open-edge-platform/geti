// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Project } from '@/api/types';

import { type ProjectActionMetadata } from '../../features/project/list/menu-actions/menu-actions.component';
import { ProjectListItem } from './project-list-item/project-list-item.component';

type ProjectListProps = {
    projects: Project[];
    onRename: (target: ProjectActionMetadata) => void;
    onDelete: (target: ProjectActionMetadata) => void;
    onEnableBlocked: (target: ProjectActionMetadata) => void;
};

export const ProjectsList = ({ projects, onRename, onDelete, onEnableBlocked }: ProjectListProps) => {
    const projectNames = projects.map(({ name }) => name);
    const projectsWithActiveProjectInFront = projects.toSorted((projectA, projectB) =>
        projectA.active_pipeline ? -1 : projectB.active_pipeline ? 1 : 0
    );

    return (
        <ul>
            {projectsWithActiveProjectInFront.map((project) => (
                <ProjectListItem
                    key={project.id}
                    project={project}
                    projectNames={projectNames.filter((name) => name !== project.name)}
                    onRename={onRename}
                    onDelete={onDelete}
                    onEnableBlocked={onEnableBlocked}
                />
            ))}
        </ul>
    );
};
