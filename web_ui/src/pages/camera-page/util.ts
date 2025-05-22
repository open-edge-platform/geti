// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { orderBy } from 'lodash-es';

import { isAnomalyDomain, isClassificationDomain } from '../../core/projects/domains';
import { Task } from '../../core/projects/task.interface';
import { getFileSize } from '../../shared/utils';
import { Screenshot, UserCameraPermission } from '../camera-support/camera.interface';

export const TOO_LOW_FREE_STORAGE_IN_BYTES = 4106127360; // 4GB, 4106127360 bytes

export const TOO_LOW_FREE_STORAGE_MESSAGE = `Your storage is running low: less than ${getFileSize(
    TOO_LOW_FREE_STORAGE_IN_BYTES
)} is available. Previous taken images/videos might be removed by the browser.`;

export const hasPermissionsDenied = (permissions: UserCameraPermission) =>
    [UserCameraPermission.ERRORED, UserCameraPermission.DENIED].includes(permissions);

export const isClassificationOrAnomaly = ({ domain }: Task) =>
    isClassificationDomain(domain) || isAnomalyDomain(domain);

// Task-chain and task different to anomaly and classification are not valid for camera feature
export const getSingleValidTask = (tasks: Task[]) =>
    tasks.length === 1 ? tasks.filter(isClassificationOrAnomaly) : [];

export enum SortingOptions {
    MOST_RECENT = 'mostRecent',
    LABEL_NAME_A_Z = 'labelNameAtoZ',
    LABEL_NAME_Z_A = 'labelNameZtoA',
}

const sortingHandlers: Record<SortingOptions, (Screenshots: Screenshot[]) => Screenshot[]> = {
    [SortingOptions.MOST_RECENT]: (Screenshots) => orderBy(Screenshots, ['file.lastModified'], 'desc'),
    [SortingOptions.LABEL_NAME_A_Z]: (Screenshots) => orderBy(Screenshots, ['labelName'], 'asc'),
    [SortingOptions.LABEL_NAME_Z_A]: (Screenshots) => orderBy(Screenshots, ['labelName'], 'desc'),
};

export const getSortingHandler = (sortingOption: SortingOptions) => sortingHandlers[sortingOption];
