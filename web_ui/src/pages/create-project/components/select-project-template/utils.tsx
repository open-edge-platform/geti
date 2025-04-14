// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Grid } from '@adobe/react-spectrum';

import {
    AnomalyClassificationImg,
    AnomalyDetectionImg,
    AnomalySegmentationImg,
    ClassificationHierarchicalImg,
    ClassificationImg,
    DetectionImg,
    DetectionRotatedImg,
    KeypointDetectionImg,
    SegmentationImg,
    SegmentationInstanceImg,
} from '../../../../assets/domains';
import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { SUBDOMAIN } from '../../../../core/projects/project.interface';
import { SingleTaskTemplateType } from '../../new-project-dialog-provider/new-project-dialog-provider.interface';
import { DomainCardsMetadata, TaskChainMetadata } from './project-template.interface';

import classes from './utils.module.scss';

const ImgBoxes = (projectSubdomain: SUBDOMAIN): JSX.Element => {
    if (projectSubdomain === SUBDOMAIN.CLASSIFICATION_MULTI_CLASS) {
        return <div className={classes.orangeBox}></div>;
    } else if (projectSubdomain === SUBDOMAIN.CLASSIFICATION_MULTI_LABEL) {
        return (
            <Flex gap={'size-50'}>
                <div className={classes.orangeBox}></div>
                <div className={classes.creamBox}></div>
                <div className={classes.energyBlueBox}></div>
            </Flex>
        );
    } else if (projectSubdomain === SUBDOMAIN.CLASSIFICATION_HIERARCHICAL) {
        return (
            <Grid gap={'size-50'} columns='auto 2fr'>
                <div className={classes.orangeBox}></div>
                <div className={classes.creamBox}></div>
                <div className={classes.energyBlueBox}></div>
                <div className={classes.lightBlueBox}></div>
            </Grid>
        );
    }

    return <></>;
};

export const TABS_SINGLE_TEMPLATE: Record<SingleTaskTemplateType, DomainCardsMetadata[]> = {
    Detection: [
        {
            TaskTypeIcon: DetectionImg,
            imgBoxes: ImgBoxes(SUBDOMAIN.DETECTION_BOUNDING_BOX),
            alt: 'detection-bounding-box',
            domain: DOMAIN.DETECTION,
            subDomain: SUBDOMAIN.DETECTION_BOUNDING_BOX,
            description: 'Draw a rectangle around an object in an image.',
            id: 'detection-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
        {
            TaskTypeIcon: DetectionRotatedImg,
            imgBoxes: ImgBoxes(SUBDOMAIN.DETECTION_ROTATED_BOUNDING_BOX),
            alt: 'detection-rotated-bounding-box',
            domain: DOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
            subDomain: SUBDOMAIN.DETECTION_ROTATED_BOUNDING_BOX,
            description: 'Draw and enclose an object within a minimal rectangle.',
            id: 'rotated-detection-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
    ],
    Segmentation: [
        {
            TaskTypeIcon: SegmentationInstanceImg,
            imgBoxes: ImgBoxes(SUBDOMAIN.SEGMENTATION_INSTANCE),
            alt: 'segmentation-instance',
            domain: DOMAIN.SEGMENTATION_INSTANCE,
            subDomain: SUBDOMAIN.SEGMENTATION_INSTANCE,
            description:
                'Detect and distinguish each individual object based on its unique features, allowing for ' +
                'identification of separate entities.',
            id: 'instance-segmentation-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
        {
            TaskTypeIcon: SegmentationImg,
            imgBoxes: ImgBoxes(SUBDOMAIN.SEGMENTATION_SEMANTIC),
            alt: 'segmentation-semantic',
            domain: DOMAIN.SEGMENTATION,
            subDomain: SUBDOMAIN.SEGMENTATION_SEMANTIC,
            description:
                'Detect and classify all similar objects as a single entity, without differentiating between ' +
                'individuals.',
            id: 'segmentation-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
    ],
    Classification: [
        {
            TaskTypeIcon: ClassificationImg,
            imgBoxes: ImgBoxes(SUBDOMAIN.CLASSIFICATION_MULTI_CLASS),
            alt: 'classification-multi-class',
            domain: DOMAIN.CLASSIFICATION,
            subDomain: SUBDOMAIN.CLASSIFICATION_MULTI_CLASS,
            description: 'Assign a label out of mutually exclusive labels.',
            id: 'classification-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
        {
            TaskTypeIcon: ClassificationImg,
            imgBoxes: ImgBoxes(SUBDOMAIN.CLASSIFICATION_MULTI_LABEL),
            alt: 'classification-multi-label',
            domain: DOMAIN.CLASSIFICATION,
            subDomain: SUBDOMAIN.CLASSIFICATION_MULTI_LABEL,
            description: 'Assign label(s) out of non-mutually exclusive labels.',
            id: 'classification-card-multi-label',
            relation: LabelsRelationType.MULTI_SELECTION,
        },
        {
            TaskTypeIcon: ClassificationHierarchicalImg,
            imgBoxes: ImgBoxes(SUBDOMAIN.CLASSIFICATION_HIERARCHICAL),
            alt: 'classification-hierarchical',
            domain: DOMAIN.CLASSIFICATION,
            subDomain: SUBDOMAIN.CLASSIFICATION_HIERARCHICAL,
            description: 'Assign label(s) with a hierarchical label structure.',
            id: 'classification-card-hierarchical',
            relation: LabelsRelationType.MIXED,
        },
    ],
    Anomaly: [
        {
            TaskTypeIcon: AnomalyClassificationImg,
            alt: 'anomaly-classification',
            domain: DOMAIN.ANOMALY_CLASSIFICATION,
            subDomain: SUBDOMAIN.ANOMALY_CLASSIFICATION,
            description: 'Categorize images as normal or anomalous.',
            id: 'anomaly-classification-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
        {
            TaskTypeIcon: AnomalyDetectionImg,
            alt: 'anomaly-detection',
            domain: DOMAIN.ANOMALY_DETECTION,
            subDomain: SUBDOMAIN.ANOMALY_DETECTION,
            description: 'Detect and categorize an object as normal or anomalous.',
            id: 'anomaly-detection-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
        {
            TaskTypeIcon: AnomalySegmentationImg,
            alt: 'anomaly-segmentation',
            domain: DOMAIN.ANOMALY_SEGMENTATION,
            subDomain: SUBDOMAIN.ANOMALY_SEGMENTATION,
            description: 'Segment and categorize an object as normal or anomalous.',
            id: 'anomaly-segmentation-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
    ],
    'Keypoint Detection': [
        {
            TaskTypeIcon: KeypointDetectionImg,
            alt: 'keypoint-detection',
            domain: DOMAIN.KEYPOINT_DETECTION,
            subDomain: SUBDOMAIN.KEYPOINT_DETECTION,
            description: 'Single object on a single image.',
            id: 'keypoints-detection-card-id',
            relation: LabelsRelationType.SINGLE_SELECTION,
        },
    ],
};

export const taskChainSubDomains: TaskChainMetadata[] = [
    {
        domains: [DOMAIN.DETECTION, DOMAIN.CLASSIFICATION],
        description:
            'Detecting objects using bounding boxes and drawing rectangles around them followed by hierarchical ' +
            'classification of the detected objects.',
        relations: [LabelsRelationType.SINGLE_SELECTION, LabelsRelationType.MIXED],
    },
    {
        domains: [DOMAIN.DETECTION, DOMAIN.SEGMENTATION],
        description:
            'Detecting objects using bounding boxes objects and drawing rectangles around them followed by semantic ' +
            'segmentation of the detected objects.',
        relations: [LabelsRelationType.SINGLE_SELECTION, LabelsRelationType.SINGLE_SELECTION],
    },
];
