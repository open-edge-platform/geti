// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { ExportFormats } from '../../../../../core/projects/dataset.interface';

export interface ExportFormatDetails {
    name: ExportFormats;
    domain: DOMAIN[];
    description: string;
}

enum DESCRIPTIONS {
    // eslint-disable-next-line max-len
    DATUMARO = `Intel's universal JSON annotation format providing dataset manipulation features; available to re-import as the original Geti project`,
    // eslint-disable-next-line max-len
    VOC = 'A common XML annotation format originally created for the Visual Object Challenge; interchange format for object detection labels',
    COCO = 'A common JSON annotation format originating from MS COCO dataset released by Microsoft in 2015',
    YOLO = 'Exports annotations in a .txt file alongside media files',
}

export const AVAILABLE_FORMATS: ExportFormatDetails[] = [
    {
        name: ExportFormats.DATUMARO,
        description: DESCRIPTIONS.DATUMARO,
        domain: [
            DOMAIN.CLASSIFICATION,
            DOMAIN.DETECTION,
            DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
            DOMAIN.SEGMENTATION,
            DOMAIN.ANOMALY_CLASSIFICATION,
            DOMAIN.ANOMALY_DETECTION,
            DOMAIN.ANOMALY_SEGMENTATION,
            DOMAIN.SEGMENTATION_INSTANCE,
            DOMAIN.KEYPOINT_DETECTION,
        ],
    },
    {
        name: ExportFormats.VOC,
        description: DESCRIPTIONS.VOC,
        domain: [
            DOMAIN.CLASSIFICATION,
            DOMAIN.DETECTION,
            DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
            DOMAIN.SEGMENTATION,
            DOMAIN.SEGMENTATION_INSTANCE,
        ],
    },
    {
        name: ExportFormats.COCO,
        description: DESCRIPTIONS.COCO,
        domain: [
            DOMAIN.DETECTION,
            DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
            DOMAIN.SEGMENTATION,
            DOMAIN.SEGMENTATION_INSTANCE,
        ],
    },
    {
        name: ExportFormats.YOLO,
        description: DESCRIPTIONS.YOLO,
        domain: [DOMAIN.DETECTION],
    },
];

export const ROTATED_BOUNDING_MESSAGE = 'Rotated bounding boxes will be converted to polygons.';

export const TASK_CHAIN_MESSAGE = 'Task-chain annotation will lose task connection.';

export const CLASSIFICATION_MESSAGE = 'Classification labels will not have relations.';

export const EXPORT_VIDEO_NOT_SUPPORTED_MESSAGE =
    // eslint-disable-next-line max-len
    'Exporting videos is not supported by this dataset format. All annotated frames from videos will be exported as images.';

export const isDatumaroFormat = (format?: ExportFormats) => format === ExportFormats.DATUMARO;
