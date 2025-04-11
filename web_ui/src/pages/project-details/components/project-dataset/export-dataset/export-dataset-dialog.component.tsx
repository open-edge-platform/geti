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

import { useState } from 'react';

import {
    ButtonGroup,
    Content,
    ContextualHelp,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Heading,
    Radio,
    RadioGroup,
    Text,
    Tooltip,
    TooltipTrigger,
} from '@adobe/react-spectrum';
import { OverlayTriggerState } from '@react-stately/overlays';
import LinkOut from '@spectrum-icons/workflow/LinkOut';

import { DOCS_BASE_URL } from '../../../../../core/const';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { ExportFormats } from '../../../../../core/projects/dataset.interface';
import { useDatasetStatistics } from '../../../../../core/statistics/hooks/use-dataset-statistics.hook';
import { ActionButton, Button } from '../../../../../shared/components/button/button.component';
import { isNotCropDomain, openNewTab, pluralize } from '../../../../../shared/utils';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';
import { useMedia } from '../../../../media/providers/media-provider.component';
import { useExportDataset } from '../../../hooks/use-export-dataset.hook';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { ExportDatasetMessage } from './export-dataset-message.component';
import { AVAILABLE_FORMATS, ExportFormatDetails, isDatumaroFormat } from './utils';

import classes from '../project-dataset.module.scss';

enum SaveVideoFormat {
    NATIVE = 'native',
    IMAGES = 'images',
}

const formatToLabel = (format: ExportFormats): string => {
    switch (format) {
        case ExportFormats.DATUMARO:
            return 'Datumaro (Recommended)';
        case ExportFormats.VOC:
            return 'VOC';
        case ExportFormats.COCO:
            return 'COCO';
        case ExportFormats.YOLO:
            return 'YOLO';
        default:
            return format;
    }
};

interface ExportDatasetDialogProps {
    triggerState: OverlayTriggerState;
    datasetName: string;
}

const ExportVideoFormatContextualHelp = () => {
    return (
        <ContextualHelp variant='info'>
            <Content>
                <Text>
                    Since your dataset contains videos, you can choose whether to keep the native video format during
                    dataset export & import (this option is only available in Datumaro format), or to convert frames to
                    individual images.
                </Text>
            </Content>
        </ContextualHelp>
    );
};

export const ExportDatasetStatistics = () => {
    const { totalVideos, totalImages } = useMedia();
    const { organizationId, workspaceId, projectId, datasetId } = useDatasetIdentifier();
    const { useGetAllTaskDatasetStatistics } = useDatasetStatistics({ allTasksStatisticsEnabled: true });
    const { data: allTasksDatasetStatistics } = useGetAllTaskDatasetStatistics({
        organizationId,
        workspaceId,
        projectId,
        datasetId,
    });

    const hasVideos = totalVideos > 0;

    return (
        <Text>
            Total: {pluralize(totalImages, 'image')}
            {hasVideos && `, ${pluralize(totalVideos, 'video')}`}
            <br />
            Annotated: {pluralize(allTasksDatasetStatistics?.overview.annotatedImages ?? 0, 'image')}
            {hasVideos && `, ${pluralize(allTasksDatasetStatistics?.overview.annotatedFrames ?? 0, 'frame')}`}
        </Text>
    );
};

export const ExportDatasetDialog = ({ triggerState, datasetName }: ExportDatasetDialogProps) => {
    const { totalVideos } = useMedia();
    const { project, isTaskChainProject } = useProject();
    const [saveVideoFormat, setSaveVideoFormat] = useState(SaveVideoFormat.IMAGES);
    const { organizationId, workspaceId, projectId, datasetId } = useDatasetIdentifier();

    const { prepareExportDatasetJob } = useExportDataset(datasetName);
    const hasVideos = totalVideos > 0;

    const matchFormats: ExportFormatDetails[] = AVAILABLE_FORMATS.filter(
        ({ name }) => saveVideoFormat === SaveVideoFormat.IMAGES || isDatumaroFormat(name)
    ).filter(({ domain }) => {
        const filteredDomains = [...domain];

        return project.domains
            .filter(isNotCropDomain)
            .every((currentDomain: DOMAIN) => filteredDomains.includes(currentDomain));
    });

    const [exportFormat, setExportFormat] = useState<ExportFormats | undefined>(matchFormats.at(0)?.name);

    const handleClose = (): void => {
        if (prepareExportDatasetJob.isPending) {
            return;
        }

        triggerState.close();

        setExportFormat(matchFormats[0]?.name);
    };

    const handleExport = () => {
        if (!exportFormat) return;

        prepareExportDatasetJob.mutate(
            {
                organizationId,
                workspaceId,
                projectId,
                datasetId,
                exportFormat,
                //we currently only support exporting videos as images,
                //if flag is off single frames + their annotations are exported
                saveVideoAsImages: hasVideos ? saveVideoFormat === SaveVideoFormat.IMAGES : true,
            },
            { onSettled: handleClose }
        );
    };

    const handleSaveVideoFormatChange = (value: string) => {
        if (value === SaveVideoFormat.NATIVE) {
            setExportFormat(ExportFormats.DATUMARO);
        }
        setSaveVideoFormat(value as SaveVideoFormat);
    };

    return (
        <DialogContainer onDismiss={handleClose}>
            {triggerState.isOpen && (
                <Dialog aria-label={'export-dataset-dialog'}>
                    <Heading>Export dataset</Heading>
                    <Divider />
                    <Content UNSAFE_className={classes.exportDialogBody}>
                        <Flex direction='column' gap={'size-200'} alignItems={'start'}>
                            <Text UNSAFE_className={classes.smallHeader}>Dataset summary</Text>
                            <ExportDatasetStatistics />
                            <Divider size='S' />
                            {hasVideos && (
                                <>
                                    <RadioGroup
                                        label={'Choose how to export videos'}
                                        contextualHelp={<ExportVideoFormatContextualHelp />}
                                        aria-label={'Videos export options'}
                                        marginTop={'size-100'}
                                        value={saveVideoFormat}
                                        onChange={handleSaveVideoFormatChange}
                                    >
                                        <Radio value={SaveVideoFormat.NATIVE}>Keep the native video format</Radio>
                                        <Radio value={SaveVideoFormat.IMAGES}>
                                            Convert frames to individual images
                                        </Radio>
                                    </RadioGroup>
                                    <Divider size='S' UNSAFE_className={classes.divider} />
                                </>
                            )}
                            <RadioGroup
                                label={'Select dataset export format'}
                                aria-label={'Export formats'}
                                value={exportFormat}
                                onChange={(format: string) => setExportFormat(format as ExportFormats)}
                            >
                                {AVAILABLE_FORMATS.map(({ name, description }: ExportFormatDetails) => {
                                    return (
                                        <TooltipTrigger key={name}>
                                            <Radio
                                                value={name}
                                                aria-label={name}
                                                isDisabled={!matchFormats.some((format) => format.name === name)}
                                            >
                                                {formatToLabel(name)}
                                            </Radio>
                                            <Tooltip>{description}</Tooltip>
                                        </TooltipTrigger>
                                    );
                                })}
                            </RadioGroup>
                            <ActionButton
                                onPress={() => openNewTab(DOCS_BASE_URL)}
                                UNSAFE_className={classes.linkButton}
                                isQuiet
                            >
                                Learn more about export formats
                                <LinkOut size='S' />
                            </ActionButton>
                            {!isDatumaroFormat(exportFormat) && (
                                <ExportDatasetMessage
                                    project={project}
                                    hasVideos={hasVideos}
                                    exportFormat={exportFormat}
                                    isTaskChainProject={isTaskChainProject}
                                />
                            )}
                        </Flex>
                    </Content>

                    <ButtonGroup isDisabled={prepareExportDatasetJob.isPending} position={'relative'}>
                        <Button variant={'secondary'} onPress={handleClose}>
                            Cancel
                        </Button>

                        <Button
                            variant={'accent'}
                            isDisabled={!exportFormat || prepareExportDatasetJob.isPending}
                            onPress={handleExport}
                            isPending={prepareExportDatasetJob.isPending}
                        >
                            Export
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
