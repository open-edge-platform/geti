// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { Flex } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import isNil from 'lodash/isNil';

import { Label } from '../../../core/labels/label.interface';
import { filterOutEmptyLabel } from '../../../core/labels/utils';
import { Loading } from '../../../shared/components/loading/loading.component';
import { getIds, hasEqualId, isNonEmptyArray } from '../../../shared/utils';
import { useTask } from '../../annotator/providers/task-provider/task-provider.component';
import { useCameraParams } from '../hooks/camera-params.hook';
import { VideoRecordingProvider } from '../providers/video-recording-provider.component';
import { getSingleValidTask } from '../util';
import { Camera } from './camera/camera.component';
import { PermissionError } from './camera/permissions-error.component';
import { LabelSelector } from './label-selector.component';
import { Sidebar } from './sidebar/sidebar.component';

import classes from './camera-page.module.scss';

interface CameraFactoryProps {
    isPermissionDenied?: boolean;
    isPermissionPending?: boolean;
}

export const CameraFactory = ({
    isPermissionDenied = false,
    isPermissionPending = true,
}: CameraFactoryProps): JSX.Element => {
    const { tasks } = useTask();
    const { isLivePrediction, defaultLabelId, hasDefaultLabel } = useCameraParams();

    const [selectedLabels, setSelectedLabels] = useState<Label[]>([]);

    const filteredTasks = getSingleValidTask(tasks);
    const taskLabels = filterOutEmptyLabel(filteredTasks.flatMap(({ labels }) => labels));
    const isValidTask = isNonEmptyArray(filteredTasks);

    if (isPermissionPending) {
        return <Loading aria-label='permissions pending' />;
    }

    if (isPermissionDenied) {
        return <PermissionError />;
    }

    if (hasDefaultLabel && isEmpty(selectedLabels)) {
        const selectedLabel = taskLabels.find(hasEqualId(defaultLabelId));

        !isNil(selectedLabel) && setSelectedLabels([selectedLabel]);
    }

    const toggleLabelSelection = (newLabels: Label[]) => {
        setSelectedLabels(newLabels);
    };

    return (
        <Flex gridArea={'content'} UNSAFE_style={{ background: 'var(--spectrum-global-color-gray-50)' }}>
            <Flex margin={'size-250'} flexGrow={1} direction={'column'} position={'relative'}>
                {isValidTask && !isLivePrediction && (
                    <LabelSelector
                        name={'Select label'}
                        maxWidth={'size-3000'}
                        selectedLabels={selectedLabels}
                        labelIds={getIds(selectedLabels)}
                        onSelectLabel={toggleLabelSelection}
                        UNSAFE_className={classes.uploadLabels}
                    />
                )}

                <VideoRecordingProvider>
                    <Camera selectedLabels={selectedLabels} />
                </VideoRecordingProvider>
            </Flex>

            <Sidebar labels={[...taskLabels]} />
        </Flex>
    );
};
