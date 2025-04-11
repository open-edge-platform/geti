// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
