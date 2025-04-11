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

import { useMemo } from 'react';

import { useSupportedAlgorithms } from '../../../core/supported-algorithms/hooks/use-supported-algorithms.hook';
import { TaskWithSupportedAlgorithms } from '../../../core/supported-algorithms/supported-algorithms.interface';
import { useProjectIdentifier } from '../../../hooks/use-project-identifier/use-project-identifier';
import { isNotCropDomain } from '../../../shared/utils';
import { useProject } from '../providers/project-provider/project-provider.component';

interface UseTasksWithSupportedAlgorithms {
    tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms;
}

export const useTasksWithSupportedAlgorithms = (): UseTasksWithSupportedAlgorithms => {
    const projectIdentifier = useProjectIdentifier();
    const {
        project: { tasks },
    } = useProject();
    const { data: supportedAlgorithms } = useSupportedAlgorithms(projectIdentifier);

    const tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms = useMemo(
        () =>
            supportedAlgorithms
                ? tasks.reduce<TaskWithSupportedAlgorithms>((prev, curr) => {
                      if (!isNotCropDomain(curr.domain)) {
                          return prev;
                      }

                      return {
                          [curr.id]: supportedAlgorithms.filter(
                              ({ domain }) => isNotCropDomain(domain) && domain === curr.domain
                          ),
                          ...prev,
                      };
                  }, {})
                : {},
        [tasks, supportedAlgorithms]
    );

    return { tasksWithSupportedAlgorithms };
};
