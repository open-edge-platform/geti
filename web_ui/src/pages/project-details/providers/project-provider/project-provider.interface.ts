// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN, ProjectIdentifier } from '../../../../core/projects/core.interface';
import { ProjectProps } from '../../../../core/projects/project.interface';

export interface ProjectContextProps {
    projectIdentifier: ProjectIdentifier;
    project: ProjectProps;
    isTaskChainProject: boolean;
    isSingleDomainProject: (domain: DOMAIN | ((domain: DOMAIN) => boolean)) => boolean;
    isTaskChainDomainProject: (domain: DOMAIN | ((domain: DOMAIN) => boolean)) => boolean;
    score: number | null;
    reload: () => void;
    error?: unknown;
}
