// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { isNotCropDomain } from '@shared/utils';

import { useSupportedAlgorithms } from '../../../core/supported-algorithms/hooks/use-supported-algorithms.hook';
import { TaskWithSupportedAlgorithms } from '../../../core/supported-algorithms/supported-algorithms.interface';
import { useProjectIdentifier } from '../../../hooks/use-project-identifier/use-project-identifier';
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
