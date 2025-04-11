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

import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';
import negate from 'lodash/negate';

import { DOMAIN } from './core.interface';
import { isAnomalyDomain, isKeypointDetection } from './domains';
import { TASK_TYPE } from './dtos/task.interface';
import { KeypointTask, Task } from './task.interface';

const TASK_TYPE_FROM_DOMAIN: Record<DOMAIN, TASK_TYPE> = {
    [DOMAIN.ANOMALY_CLASSIFICATION]: TASK_TYPE.ANOMALY_CLASSIFICATION,
    [DOMAIN.ANOMALY_DETECTION]: TASK_TYPE.ANOMALY_DETECTION,
    [DOMAIN.ANOMALY_SEGMENTATION]: TASK_TYPE.ANOMALY_SEGMENTATION,
    [DOMAIN.DETECTION]: TASK_TYPE.DETECTION,
    [DOMAIN.DETECTION_ROTATED_BOUNDING_BOX]: TASK_TYPE.DETECTION_ROTATED_BOUNDING_BOX,
    [DOMAIN.CROP]: TASK_TYPE.CROP,
    [DOMAIN.SEGMENTATION]: TASK_TYPE.SEGMENTATION,
    [DOMAIN.SEGMENTATION_INSTANCE]: TASK_TYPE.SEGMENTATION_INSTANCE,
    [DOMAIN.CLASSIFICATION]: TASK_TYPE.CLASSIFICATION,
    [DOMAIN.KEYPOINT_DETECTION]: TASK_TYPE.KEYPOINT_DETECTION,
};

export const getTaskTypeFromDomain = (domain: DOMAIN, anomalyRevampFlagEnabled = false): TASK_TYPE => {
    if (anomalyRevampFlagEnabled && isAnomalyDomain(domain)) {
        return TASK_TYPE.ANOMALY;
    }

    return TASK_TYPE_FROM_DOMAIN[domain];
};

export const getRoundedProgress = (progress: number): string => {
    return progress > 0 ? `${progress > 99 ? Math.floor(progress) : Math.round(progress)}%` : '0%';
};

export const getFormattedTimeRemaining = (time: number): string | undefined => {
    dayjs.extend(duration);
    dayjs.extend(relativeTime);

    if (time <= 0) {
        return undefined;
    }

    const totalDuration = dayjs.duration(time * 1000); // convert to milliseconds
    const days = totalDuration.days() > 0 ? `${totalDuration.days()} days, ` : '';
    const hours = totalDuration.hours() > 0 ? `${totalDuration.hours()}h:` : '';
    const minutes = totalDuration.minutes() > 0 ? `${totalDuration.minutes()}m:` : '';
    const seconds = totalDuration.seconds() > 0 ? `${totalDuration.seconds()}s` : '';

    // e.g. 7 days, 4h:30m:25s
    return `${days}${hours}${minutes}${seconds}`;
};

export const isKeypointTask = (task: Task): task is KeypointTask => isKeypointDetection(task.domain);
export const isNotKeypointTask = negate(isKeypointTask);
