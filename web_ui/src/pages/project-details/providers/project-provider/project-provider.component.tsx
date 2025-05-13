// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useCallback, useContext } from 'react';

import { isFunction } from 'lodash-es';
import { useErrorHandler } from 'react-error-boundary';

import { DOMAIN, ProjectIdentifier } from '../../../../core/projects/core.interface';
import { useProjectActions } from '../../../../core/projects/hooks/use-project-actions.hook';
import { useUserProjectSettings } from '../../../../core/user-settings/hooks/use-project-settings.hook';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { isNotCropDomain } from '../../../../shared/utils';
import { ProjectContextProps } from './project-provider.interface';

const ProjectContext = createContext<ProjectContextProps | undefined>(undefined);

interface ProjectProviderProps {
    children: ReactNode;
    projectIdentifier: ProjectIdentifier;
}

export const ProjectProvider = ({ projectIdentifier, children }: ProjectProviderProps): JSX.Element => {
    const { useSuspenseGetProject } = useProjectActions();
    const { data: project, error: ProjectError, refetch } = useSuspenseGetProject(projectIdentifier);
    const isTaskChainProject = Boolean(project && project.tasks.length > 1);

    const isSingleDomainProject = useCallback(
        (domain: DOMAIN | ((domain: DOMAIN) => boolean)) => {
            if (project === undefined || isTaskChainProject) {
                return false;
            }

            const domains = project.tasks.map((task) => task.domain);

            if (isFunction(domain)) {
                return domain(domains[0]);
            }

            return domains[0] === domain;
        },
        [isTaskChainProject, project]
    );

    const isTaskChainDomainProject = useCallback(
        (domain: DOMAIN | ((domain: DOMAIN) => boolean)) => {
            if (project === undefined || !isTaskChainProject) {
                return false;
            }

            const domains = project.tasks.map((task) => task.domain).filter(isNotCropDomain);

            if (isFunction(domain)) {
                return domain(domains[0]) || domain(domains[1]);
            }

            return domains.some((domainItem) => domainItem === domain);
        },
        [isTaskChainProject, project]
    );

    useErrorHandler(ProjectError);

    // We want to make sure that the project settings are loaded by react-query
    // this prevents a flickering layout in the annotator
    useUserProjectSettings(projectIdentifier);

    if (project === undefined) {
        // Trigger suspense
        throw new Promise(() => {
            return 'loading project';
        });
    }

    const score =
        project.performance.type === 'default_performance'
            ? project.performance.score
            : project.performance.globalScore;

    const value: ProjectContextProps = {
        projectIdentifier,
        project,
        isTaskChainProject,
        isSingleDomainProject,
        isTaskChainDomainProject,
        error: ProjectError,
        score: score !== null ? Math.round(score) : null,
        reload: refetch,
    };

    return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
};

export const useProject = (): ProjectContextProps => {
    const context = useContext(ProjectContext);

    if (context === undefined) {
        throw new MissingProviderError('useProject', 'ProjectProvider');
    }

    return context;
};
