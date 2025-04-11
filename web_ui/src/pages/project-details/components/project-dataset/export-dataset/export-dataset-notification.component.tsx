// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect } from 'react';

import { View } from '@adobe/react-spectrum';
import { OverlayTriggerState, useOverlayTriggerState } from '@react-stately/overlays';

import { DatasetIdentifier, ExportDatasetLSData } from '../../../../../core/projects/dataset.interface';
import { useLocalStorageExportDataset } from '../../../hooks/use-local-storage-export-dataset.hook';
import { ExportDatasetDownload } from './export-dataset-download.component';
import { ExportDatasetStatusJob } from './export-dataset-status-job.component';

interface ExportDatasetStatusProps {
    datasetIdentifier: DatasetIdentifier;
    visibilityState: OverlayTriggerState;
}

const useReopen = (
    datasetLsData: ExportDatasetLSData | undefined,
    visibilityState: OverlayTriggerState,
    downloadState: OverlayTriggerState,
    statusState: OverlayTriggerState
) => {
    useEffect(() => {
        if (!datasetLsData) {
            return;
        }
        // Open it back after, for instance on page reload
        if (!visibilityState.isOpen) {
            visibilityState.open();
        }

        datasetLsData.isPrepareDone ? downloadState.open() : statusState.open();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [visibilityState.isOpen]);
};

export const ExportDatasetNotification = ({ datasetIdentifier, visibilityState }: ExportDatasetStatusProps) => {
    const statusState = useOverlayTriggerState({});
    const downloadState = useOverlayTriggerState({});
    const { datasetId } = datasetIdentifier;

    const { getDatasetLsByDatasetId, updateLsExportDataset, removeDatasetLsByDatasetId } =
        useLocalStorageExportDataset();
    const localStorageData = getDatasetLsByDatasetId(datasetId);

    useReopen(localStorageData, visibilityState, downloadState, statusState);

    const onPrepareDone = (lsData: ExportDatasetLSData) => {
        statusState.close();
        downloadState.open();
        updateLsExportDataset({ ...lsData, isPrepareDone: true });
    };

    const close = (componentState: OverlayTriggerState) => (datasetID: string) => {
        removeDatasetLsByDatasetId(datasetID);
        componentState.close();
        visibilityState.close();
    };

    if (!visibilityState.isOpen || !localStorageData) {
        return <></>;
    }

    return (
        <View aria-label='export-dataset-notifications'>
            {statusState.isOpen && (
                <ExportDatasetStatusJob
                    datasetIdentifier={datasetIdentifier}
                    onCloseStatus={close(statusState)}
                    onPrepareDone={onPrepareDone}
                    localStorageData={localStorageData}
                />
            )}
            {downloadState.isOpen && (
                <ExportDatasetDownload localStorageData={localStorageData} onCloseDownload={close(downloadState)} />
            )}
        </View>
    );
};
