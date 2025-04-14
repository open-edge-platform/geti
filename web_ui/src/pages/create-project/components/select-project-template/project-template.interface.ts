// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, SVGProps } from 'react';

import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { SUBDOMAIN } from '../../../../core/projects/project.interface';
import { TaskMetadata } from '../../../../core/projects/task.interface';

export interface SingleTemplateProps {
    cards: DomainCardsMetadata[];
    metaData?: TaskMetadata;
    setSelectedDomains: (domains: DOMAIN[], relations: LabelsRelationType[]) => void;
}

export interface TaskChainTemplateProps {
    subDomains: TaskChainMetadata[];
    selectedDomains: DOMAIN[];
    setSelectedDomains: (domains: DOMAIN[], relations: LabelsRelationType[]) => void;
}
export interface DomainCardsMetadata {
    alt: string;
    id: string;
    domain: DOMAIN;
    subDomain: SUBDOMAIN;
    relation: LabelsRelationType;
    TaskTypeIcon: FC<SVGProps<SVGSVGElement>> | string;
    imgBoxes?: JSX.Element;
    description: string;
    disabled?: boolean;
}

export interface TaskChainMetadata {
    domains: DOMAIN[];
    relations: LabelsRelationType[];
    description: string;
}
