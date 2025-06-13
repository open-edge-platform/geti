// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { useNavigateToAnnotatorRoute } from '@geti/core/src/services/use-navigate-to-annotator-route.hook';
import { Button, Flex, Item, TabList, TabPanels, Tabs, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import { useNavigate } from 'react-router-dom';
import { useOverlayTriggerState } from 'react-stately';

import { Dataset } from '../../../../core/projects/dataset.interface';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { FUX_NOTIFICATION_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { ExportDatasetNotification } from '../../../../features/dataset-export/components/export-dataset-notification.component';
import { ExportImportDatasetButtons } from '../../../../features/dataset-export/components/export-import-dataset-buttons.component';
import { useLocalStorageExportDataset } from '../../../../features/dataset-export/hooks/use-local-storage-export-dataset.hook';
import { DatasetImports } from '../../../../features/dataset-import/components/dataset-import-to-existing-project/dataset-imports.component';
import { CoachMark } from '../../../../shared/components/coach-mark/coach-mark.component';
import { TooltipWithDisableButton } from '../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { TabItem } from '../../../../shared/components/tabs/tabs.interface';
import { TruncatedText } from '../../../../shared/components/truncated-text/truncated-text.component';
import { useActiveTab } from '../../../../shared/hooks/use-active-tab.hook';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { useMedia } from '../../../media/providers/media-provider.component';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { ChildrenTabs } from './children-tabs.component';
import { useOpenNotificationToast } from './hooks/open-notification-toast.hook';
import { DATASET_TABS_TO_PATH, DatasetChapters, NO_MEDIA_MESSAGE } from './utils';

import classes from './project-dataset.module.scss';

export const DatasetTabPanel = ({ dataset }: { dataset: Dataset }) => {
    const navigate = useNavigate();
    const { media } = useMedia();
    const selectedDataset = dataset;
    const datasetIdentifier = useDatasetIdentifier();
    const exportNotificationState = useOverlayTriggerState({});
    const { getDatasetLsByDatasetId } = useLocalStorageExportDataset();

    const { projectIdentifier, isSingleDomainProject } = useProject();
    const navigateToAnnotatorRoute = useNavigateToAnnotatorRoute();

    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);

    const hasMediaItems = !isEmpty(media);
    const activeTab = useActiveTab(DatasetChapters.MEDIA);

    const isAnnotatorDisabled = !hasMediaItems;
    const tooltipText = isAnnotatorDisabled ? NO_MEDIA_MESSAGE : undefined;

    const annotateButtonText = isAnomalyProject
        ? 'Explore'
        : selectedDataset.useForTraining
          ? 'Annotate interactively'
          : `Annotate ${selectedDataset.name}`;

    const handleGoToAnnotator = () => {
        navigateToAnnotatorRoute({
            datasetIdentifier: { ...projectIdentifier, datasetId: selectedDataset.id },
            active: selectedDataset.useForTraining && !isAnomalyProject,
        });
    };

    useOpenNotificationToast();

    return (
        <Flex position='relative' height='100%' direction={'column'} UNSAFE_style={{ boxSizing: 'border-box' }}>
            <DatasetImports />

            <ExportDatasetNotification
                // We use the key to refresh the component state whenever the export instance per dataset
                // has changed
                key={getDatasetLsByDatasetId(dataset.id)?.exportDatasetId}
                datasetIdentifier={datasetIdentifier}
                visibilityState={exportNotificationState}
            />
            <Flex height='100%' direction={'column'} flex={1} minHeight={0}>
                <Tabs
                    isQuiet
                    items={ChildrenTabs()}
                    disabledKeys={hasMediaItems ? [] : [DatasetChapters.STATISTICS]}
                    selectedKey={activeTab}
                    height='100%'
                    aria-label='Dataset page sub tabs'
                    onSelectionChange={(key: Key) => {
                        navigate(
                            DATASET_TABS_TO_PATH[key as DatasetChapters]({
                                ...projectIdentifier,
                                datasetId: selectedDataset.id,
                            })
                        );
                    }}
                >
                    <Flex alignItems={'center'} justifyContent={'space-between'} marginY={'size-100'}>
                        <TabList UNSAFE_className={classes.childrenTabList}>
                            {(item: TabItem) => <Item textValue={item.name as string}>{item.name}</Item>}
                        </TabList>
                        <Flex gap='size-100'>
                            {isAnomalyProject && <ExportImportDatasetButtons hasMediaItems={hasMediaItems} />}
                            <View>
                                {annotateButtonText === 'Annotate interactively' && !isAnnotatorDisabled && (
                                    <CoachMark
                                        settingsKey={FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY}
                                        styles={{
                                            position: 'absolute',
                                            zIndex: '5',
                                            top: '-58px',
                                            right: '55px',
                                            maxWidth: '100%',
                                        }}
                                    />
                                )}

                                <TooltipWithDisableButton activeTooltip={tooltipText} disabledTooltip={tooltipText}>
                                    <Button
                                        id={'annotate-button-id'}
                                        variant={'accent'}
                                        onPress={handleGoToAnnotator}
                                        UNSAFE_style={{ display: 'block' }}
                                        isDisabled={isAnnotatorDisabled}
                                    >
                                        <TruncatedText>{annotateButtonText}</TruncatedText>
                                    </Button>
                                </TooltipWithDisableButton>
                            </View>
                        </Flex>
                    </Flex>

                    <TabPanels minHeight={0} UNSAFE_style={{ overflowY: 'auto' }}>
                        {(item: TabItem) => <Item textValue={item.key}>{item.children}</Item>}
                    </TabPanels>
                </Tabs>
            </Flex>
        </Flex>
    );
};
