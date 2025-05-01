// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { LOCAL_STORAGE_KEYS } from '@shared/local-storage-keys';
import { getParsedLocalStorage } from '@shared/utils';
import { useLocalStorage } from 'usehooks-ts';

import { ProjectIdentifier } from '../../../core/projects/core.interface';
import { ExportDatasetLSData } from '../../../core/projects/dataset.interface';
import { useProjectIdentifier } from '../../../hooks/use-project-identifier/use-project-identifier';

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
