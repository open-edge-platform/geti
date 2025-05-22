// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Flex, Loading } from '@geti/ui';
import { isEmpty, isNil } from 'lodash-es';

import { Label } from '../../../core/labels/label.interface';
import { filterOutEmptyLabel } from '../../../core/labels/utils';
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
