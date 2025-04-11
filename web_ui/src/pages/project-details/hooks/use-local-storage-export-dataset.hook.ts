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

import { useLocalStorage } from 'usehooks-ts';

import { ProjectIdentifier } from '../../../core/projects/core.interface';
import { ExportDatasetLSData } from '../../../core/projects/dataset.interface';
import { useProjectIdentifier } from '../../../hooks/use-project-identifier/use-project-identifier';
import { LOCAL_STORAGE_KEYS } from '../../../shared/local-storage-keys';
import { getParsedLocalStorage } from '../../../shared/utils';

const isDatasetDifferentTo =
    (value: string) =>
    ({ datasetId }: ExportDatasetLSData) =>
        datasetId !== value;

const getDatasetExportKey = ({ organizationId, workspaceId, projectId }: ProjectIdentifier): string => {
    return `${LOCAL_STORAGE_KEYS.EXPORTING_DATASETS}-${organizationId}-${workspaceId}-${projectId}`;
};

const geDatasetsFromLS = (projectIdentifier: ProjectIdentifier): ExportDatasetLSData[] => {
    const datasetExportInProjectContext = getParsedLocalStorage<ExportDatasetLSData[]>(
        getDatasetExportKey(projectIdentifier)
    );

    if (datasetExportInProjectContext === null) {
        return getParsedLocalStorage<ExportDatasetLSData[]>(LOCAL_STORAGE_KEYS.EXPORTING_DATASETS) ?? [];
    }

    return datasetExportInProjectContext ?? [];
};

const updateDatasetLs = (
    lsDatasetInfo: ExportDatasetLSData[],
    newExportingDataset: ExportDatasetLSData
): ExportDatasetLSData[] => {
    const filterDatasets = lsDatasetInfo.filter(isDatasetDifferentTo(newExportingDataset.datasetId));
    return [...filterDatasets, newExportingDataset];
};

export const useLocalStorageExportDataset = () => {
    const projectIdentifier = useProjectIdentifier();

    const [lsExportDataset, setLSExportDataset] = useLocalStorage<ExportDatasetLSData[]>(
        getDatasetExportKey(projectIdentifier),
        geDatasetsFromLS(projectIdentifier)
    );
    const hasLocalstorageDataset = (datasetId: string): boolean => Boolean(getDatasetLsByDatasetId(datasetId));

    const getDatasetLsByDatasetId = (queryDatasetId: string): ExportDatasetLSData | undefined =>
        geDatasetsFromLS(projectIdentifier).find(({ datasetId }) => datasetId === queryDatasetId);

    const addLsExportDataset = (data: ExportDatasetLSData): void =>
        // we don't want to have more than one instance of export per dataset
        setLSExportDataset([...geDatasetsFromLS(projectIdentifier).filter(isDatasetDifferentTo(data.datasetId)), data]);

    const updateLsExportDataset = (data: ExportDatasetLSData): void =>
        setLSExportDataset(updateDatasetLs(lsExportDataset, data));

    const removeDatasetLsByDatasetId = (queryDatasetId: string): ExportDatasetLSData[] => {
        const lsDatasetInfo = geDatasetsFromLS(projectIdentifier);
        const finalData = !hasLocalstorageDataset(queryDatasetId)
            ? lsDatasetInfo
            : lsDatasetInfo.filter(isDatasetDifferentTo(queryDatasetId));

        setLSExportDataset(finalData);

        return finalData;
    };

    return {
        hasLocalstorageDataset,
        addLsExportDataset,
        updateLsExportDataset,
        getDatasetLsByDatasetId,
        removeDatasetLsByDatasetId,
    };
};
