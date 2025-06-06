// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, ReactNode, SetStateAction } from 'react';

import { Item, TabList, TabPanels, Tabs } from '@geti/ui';
import { isEmpty, isNil } from 'lodash-es';

import { DATASET_IMPORT_TO_NEW_PROJECT_STEP } from '../../../../../core/datasets/dataset.enum';
import { DatasetImportToNewProjectItem } from '../../../../../core/datasets/dataset.interface';
import { hasKeypointStructure } from '../../../../../providers/dataset-import-to-new-project-provider/utils';
import { DatasetImportDnd } from '../../../../../shared/components/dataset-import-dnd/dataset-import-dnd.component';
import { DatasetImportProgress } from '../../../../../shared/components/dataset-import-progress/dataset-import-progress.component';
import { DatasetImportWarnings } from '../../../../../shared/components/dataset-import-warnings/dataset-import-warnings.component';
import { DatasetImportToNewProjectDomain } from './dataset-import-to-new-project-domain.component';
import { DatasetImportToNewProjectLabels } from './dataset-import-to-new-project-labels.component';

interface DatasetImportToNewProjectDialogContentTabsProps {
    children: ReactNode;
}

const DatasetImportToNewProjectDialogContentTabs = ({
    children,
}: DatasetImportToNewProjectDialogContentTabsProps): JSX.Element => {
    return (
        <Tabs aria-label='Dataset import tabs' height={'100%'}>
            <TabList>
                <Item key='upload'>Upload</Item>
            </TabList>
            <TabPanels>
                <Item key='upload'>{children}</Item>
            </TabPanels>
        </Tabs>
    );
};

interface DatasetImportToNewProjectDialogContentProps {
    datasetImportItem: DatasetImportToNewProjectItem | undefined;
    prepareDataset: (file: File) => string | undefined;
    patchDatasetImport: (item: Partial<DatasetImportToNewProjectItem>) => void;
    setActiveDatasetImportId: Dispatch<SetStateAction<string | undefined>>;
    anomalyRevamp: boolean;
}

export const DatasetImportToNewProjectDialogContent = ({
    datasetImportItem,
    prepareDataset,
    patchDatasetImport,
    setActiveDatasetImportId,
    anomalyRevamp,
}: DatasetImportToNewProjectDialogContentProps): JSX.Element => {
    const isKeypointImport = datasetImportItem && hasKeypointStructure(datasetImportItem.supportedProjectTypes);

    if (isNil(datasetImportItem)) {
        return (
            <DatasetImportToNewProjectDialogContentTabs>
                <DatasetImportDnd setUploadItem={prepareDataset} setActiveUploadId={setActiveDatasetImportId} />
            </DatasetImportToNewProjectDialogContentTabs>
        );
    }

    return (
        <>
            {datasetImportItem.activeStep === DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET && (
                <DatasetImportToNewProjectDialogContentTabs>
                    {isEmpty(datasetImportItem.warnings) ? (
                        <DatasetImportProgress progressItem={datasetImportItem} />
                    ) : (
                        <DatasetImportWarnings warnings={datasetImportItem.warnings} />
                    )}
                </DatasetImportToNewProjectDialogContentTabs>
            )}
            {datasetImportItem.activeStep === DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN && (
                <DatasetImportToNewProjectDomain
                    datasetImportItem={datasetImportItem}
                    patchDatasetImport={patchDatasetImport}
                    anomalyRevamp={anomalyRevamp}
                />
            )}
            {datasetImportItem.activeStep === DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS && (
                <DatasetImportToNewProjectLabels
                    hasCheckbox={!isKeypointImport}
                    datasetImportItem={datasetImportItem}
                    patchDatasetImport={patchDatasetImport}
                />
            )}
        </>
    );
};
