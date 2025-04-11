// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { separateGroup } from '../../../../../core/labels/annotator-utils/group-utils';
import { fetchLabelsTreeWithGroups } from '../../../../../core/labels/annotator-utils/labels-utils';
import { Readonly } from '../../../../../core/labels/label-tree-view.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { filterOutEmptyLabel } from '../../../../../core/labels/utils';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { ProjectTaskLabels } from '../../project-labels/project-task-labels/project-task-labels.component';
import { getRelation } from '../../project-labels/utils';

interface ModelLabelsProps {
    labels: Label[];
    domain?: DOMAIN;
}

export const ModelLabels = ({ labels, domain }: ModelLabelsProps): JSX.Element => {
    const { project, isTaskChainProject } = useProject();

    const filteredLabels = filterOutEmptyLabel(labels);

    // Note: I'm assuming that first label is the "root" one for the model
    const level = separateGroup(labels[0].group).length;
    const labelsTree = fetchLabelsTreeWithGroups(filteredLabels, 'all', null, null, level);
    const relation = getRelation(labels, domain ? [domain] : project.domains);

    return (
        <ProjectTaskLabels
            task={{ domain: domain ?? project.domains[0], labels: labelsTree, relation }}
            isTaskChainProject={isTaskChainProject}
            type={Readonly.YES}
        />
    );
};
