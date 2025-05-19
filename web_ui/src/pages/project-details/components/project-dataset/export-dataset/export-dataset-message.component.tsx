// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text } from '@geti/ui';

import { Alert } from '../../../../../assets/icons';
import { ExportFormats } from '../../../../../core/projects/dataset.interface';
import { isClassificationDomain, isRotatedDetectionDomain } from '../../../../../core/projects/domains';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import {
    CLASSIFICATION_MESSAGE,
    EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE,
    ROTATED_BOUNDING_MESSAGE,
    TASK_CHAIN_MESSAGE,
} from './utils';

import classes from '../project-dataset.module.scss';

interface ExportDatasetMessageProps {
    project: ProjectProps;
    hasVideos: boolean;
    exportFormat: ExportFormats | undefined;
    isTaskChainProject?: boolean;
}

export const ExportDatasetMessage = ({
    project,
    hasVideos,
    exportFormat,
    isTaskChainProject = false,
}: ExportDatasetMessageProps) => {
    const isClassification = project.domains.some(isClassificationDomain);
    const isRotatedDetection = project.domains.some(isRotatedDetectionDomain);

    const isClassificationExportingVoc = isClassification && exportFormat === ExportFormats.VOC;

    const isNotDatumaroRotatedDetection =
        isRotatedDetection && !!exportFormat && exportFormat !== ExportFormats.DATUMARO;

    const isTaskChainVocOrCoco =
        isTaskChainProject && (exportFormat === ExportFormats.VOC || exportFormat === ExportFormats.COCO);

    const hasMessages = [
        hasVideos,
        isTaskChainVocOrCoco,
        isClassificationExportingVoc,
        isNotDatumaroRotatedDetection,
    ].includes(true);

    if (!hasMessages) {
        return null;
    }

    return (
        <>
            <Text UNSAFE_className={classes.messages}>
                <Alert /> Converted formats
            </Text>

            <ul className={classes.messageList}>
                {isClassificationExportingVoc && <li>{CLASSIFICATION_MESSAGE}</li>}

                {isNotDatumaroRotatedDetection && <li>{ROTATED_BOUNDING_MESSAGE}</li>}

                {isTaskChainVocOrCoco && <li>{TASK_CHAIN_MESSAGE}</li>}

                {hasVideos && <li>{EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE}</li>}
            </ul>
        </>
    );
};
