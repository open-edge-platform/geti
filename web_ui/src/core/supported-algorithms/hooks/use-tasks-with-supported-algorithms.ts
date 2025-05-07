// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useProjectIdentifier } from '../../../hooks/use-project-identifier/use-project-identifier';
import { isNotCropDomain } from '../../../shared/utils';
import { useProjectActions } from '../../projects/hooks/use-project-actions.hook';
import { TaskWithSupportedAlgorithms } from '../supported-algorithms.interface';
import { useSupportedAlgorithms } from './use-supported-algorithms.hook';

interface UseTasksWithSupportedAlgorithms {
    tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms;
}

export const useTasksWithSupportedAlgorithms = (): UseTasksWithSupportedAlgorithms => {
    const projectIdentifier = useProjectIdentifier();
    const { useGetProject } = useProjectActions();
    const { data: project } = useGetProject(projectIdentifier);

    const { data: supportedAlgorithms } = useSupportedAlgorithms(projectIdentifier);

    const tasksWithSupportedAlgorithms: TaskWithSupportedAlgorithms = useMemo(() => {
        if (supportedAlgorithms === undefined || project?.tasks === undefined) {
            return {};
        }

        return project.tasks.reduce<TaskWithSupportedAlgorithms>((prev, curr) => {
            if (!isNotCropDomain(curr.domain)) {
                return prev;
            }

            return {
                [curr.id]: supportedAlgorithms.filter(
                    ({ domain }) => isNotCropDomain(domain) && domain === curr.domain
                ),
                ...prev,
            };
        }, {});
    }, [project?.tasks, supportedAlgorithms]);

    return { tasksWithSupportedAlgorithms };
};
