// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isKeypointDetection } from '../../../../../core/projects/domains';
import { useProject } from '../../../providers/project-provider/project-provider.component';

export const useIsExplanationEnabled = (imageWasUploaded: boolean) => {
    const { isTaskChainProject, isSingleDomainProject } = useProject();
    if (imageWasUploaded === false) {
        return false;
    }

    return isTaskChainProject === false && isSingleDomainProject(isKeypointDetection) === false;
};
