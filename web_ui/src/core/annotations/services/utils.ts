// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isObject from 'lodash/isObject';
import sortBy from 'lodash/sortBy';
import { v4 as uuidv4 } from 'uuid';

import { hasEqualId } from '../../../shared/utils';
import { Label } from '../../labels/label.interface';
import { isPrediction } from '../../labels/utils';
import { isImage } from '../../media/image.interface';
import { MediaItem } from '../../media/media.interface';
import { isVideo } from '../../media/video.interface';
import { DatasetIdentifier } from '../../projects/dataset.interface';
import { Annotation, AnnotationLabel, KeypointAnnotation } from '../annotation.interface';
import {
    AnnotationDTO,
    AnnotationLabelDTO,
    ImageIdDTO,
    KeypointAnnotationDTO,
    SHAPE_TYPE_DTO,
    ShapeDTO,
    VideoFrameIdDTO,
} from '../dtos/annotation.interface';
import {
    ExplanationDTO,
    KeypointPredictionDTO,
    NewExplanationsDTO,
    NewKeypointPredictionDTO,
    NewPredictionLabelDTO,
    NewPredictionsDTO,
    PredictionDTO,
} from '../dtos/prediction.interface';
import { Explanation } from '../prediction.interface';
import { Rect, Shape } from '../shapes.interface';
import { ShapeType } from '../shapetype.enum';
import { hasMaxAllowedAnnotations, isPoseShape, labelFromUser, MAX_SUPPORTED_ANNOTATIONS } from '../utils';
import { PredictionCache, PredictionMode } from './prediction-service.interface';

// Since predictions can take a while to load we want to throw a timeout exception
// if they aren't returned in proper time (in this case 60 seconds)
export const PREDICTION_TIMEOUT = 60_000;

export interface PredictionParams {
    dataset_id: string;
    image_id?: string;
    video_id?: string;
    frame_index?: string;
    end_frame?: string;
    frame_skip?: string;
    start_frame?: string;
}

const getShape = (shape: ShapeDTO): Shape => {
    switch (shape.type) {
        case SHAPE_TYPE_DTO.RECTANGLE: {
            return {
                shapeType: ShapeType.Rect,
                x: shape.x,
                y: shape.y,
                width: shape.width,
                height: shape.height,
            };
        }

        case SHAPE_TYPE_DTO.ROTATED_RECTANGLE: {
            return {
                shapeType: ShapeType.RotatedRect,
                angle: shape.angle,
                x: shape.x,
                y: shape.y,
                width: shape.width,
                height: shape.height,
            };
        }

        case SHAPE_TYPE_DTO.ELLIPSE: {
            // The server returns the bounding box of the circle
            const rWidth = shape.width / 2;
            const rHeight = shape.height / 2;

            return {
                shapeType: ShapeType.Circle,
                x: shape.x + rWidth,
                y: shape.y + rHeight,
                r: Math.max(rWidth, rHeight),
            };
        }

        case SHAPE_TYPE_DTO.POLYGON: {
            return {
                shapeType: ShapeType.Polygon,
                points: shape.points,
            };
        }

        case SHAPE_TYPE_DTO.KEYPOINT: {
            return {
                shapeType: ShapeType.Pose,
                points: [],
            };
        }
    }
};

export const convertPredictionLabelDTO = ({
    id,
    probability,
}: Omit<NewPredictionLabelDTO, 'name'>): AnnotationLabelDTO => ({
    id,
    probability,
    source: { model_id: 'latest', user_id: null, model_storage_id: 'storage_id' },
});

export const convertLabelToDTO = ({ id, source }: AnnotationLabel): AnnotationLabelDTO => ({
    id,
    probability: 1,
    source: {
        user_id: source.userId ?? null,
        model_id: source.modelId ?? null,
        model_storage_id: source.modelStorageId ?? null,
    },
});

export const isKeypointPredictionDTO = (obj: unknown): obj is NewKeypointPredictionDTO => {
    return isObject(obj) && 'keypoints' in obj && Array.isArray(obj.keypoints);
};

export const formatKeypointToAnnotationDTO =
    (modified: string) =>
    ({ id, score, x, y }: KeypointPredictionDTO): AnnotationDTO => {
        return {
            id: uuidv4(),
            shape: { x, y, is_visible: true, type: SHAPE_TYPE_DTO.KEYPOINT },
            labels: [convertPredictionLabelDTO({ id, probability: score })],
            labels_to_revisit: [],
            modified,
        };
    };

export const convertPredictionsDTO = (
    new_predictions: NewPredictionsDTO,
    media_identifier: ImageIdDTO | VideoFrameIdDTO
    // some source implementation
): PredictionDTO => {
    const annotations = new_predictions.predictions.flatMap((prediction): AnnotationDTO[] => {
        if (isKeypointPredictionDTO(prediction)) {
            return prediction.keypoints.map(formatKeypointToAnnotationDTO(new_predictions.created));
        }

        return [
            {
                id: uuidv4(),
                labels: prediction.labels.map(convertPredictionLabelDTO),
                shape: prediction.shape,
                labels_to_revisit: [],
                modified: new_predictions.created,
            },
        ];
    });

    return {
        id: uuidv4(),
        kind: 'prediction',
        maps: [],
        media_identifier,
        modified: new_predictions.created,
        annotations,
    };
};

export const convertExplanationsDTO = (
    new_explanations: NewExplanationsDTO,
    { id: roiId, ...roiConfig }: Omit<Rect, 'shapeType'> & { id: string }
): ExplanationDTO[] => {
    return new_explanations.maps.map(({ label_id, label_name, data }) => ({
        id: uuidv4(),
        label_id,
        name: label_name,
        url: '',
        binary: data,
        roi: {
            id: roiId,
            //TODO: delete shape type, update mocks and unit tests related
            shape: { ...roiConfig, type: ShapeType.Rect.toString() },
        },
    }));
};

export const getAnnotation = (annotation: AnnotationDTO, projectLabels: Label[], index: number): Annotation => {
    const labels = annotation.labels
        .map((label: AnnotationLabelDTO): AnnotationLabel | undefined => {
            const projectLabel = projectLabels.find(hasEqualId(label.id));

            if (projectLabel === undefined) {
                return undefined;
            }

            const {
                id,
                probability,
                source: { user_id, model_id, model_storage_id },
            } = label;
            const { name, color, hotkey, group, parentLabelId, behaviour, isEmpty } = projectLabel;

            return {
                id,
                name,
                color,
                group,
                parentLabelId: parentLabelId || null,
                source: {
                    userId: user_id ?? undefined,
                    modelId: model_id ?? undefined,
                    modelStorageId: model_storage_id ?? undefined,
                },
                score: user_id && !model_id ? undefined : probability,
                hotkey,
                behaviour,
                isEmpty,
            };
        })
        .filter((label): label is AnnotationLabel => label !== undefined);

    // The server does not guarantee that labels are sorted by hierarchy
    const sortedLabels = sortBy(labels, (label) => projectLabels.findIndex(hasEqualId(label.id)));

    const shape = getShape(annotation.shape);

    return {
        id: annotation.id,
        isHidden: false,
        isSelected: false,
        isLocked: false,
        labels: sortedLabels,
        shape,
        zIndex: index,
    };
};

export const isKeypointAnnotationDTO = (annotation: AnnotationDTO): annotation is KeypointAnnotationDTO => {
    return annotation.shape.type === SHAPE_TYPE_DTO.KEYPOINT;
};

export const getKeypointAnnotation = (annotations: KeypointAnnotationDTO[], projectLabels: Label[]) => {
    const [firstAnnotation, ...otherAnnotations] = annotations;
    const initialAnnotation = getAnnotation(firstAnnotation, projectLabels, 0) as KeypointAnnotation;

    initialAnnotation.shape.points.push({
        x: firstAnnotation.shape.x,
        y: firstAnnotation.shape.y,
        label: initialAnnotation.labels[0],
        isVisible: firstAnnotation.shape.is_visible,
    });

    return otherAnnotations.reduce((baseAnnotation, current) => {
        const currentAnnotation = getAnnotation(current, projectLabels, 0);

        baseAnnotation.shape.points.push({
            x: current.shape.x,
            y: current.shape.y,
            label: currentAnnotation.labels[0],
            isVisible: current.shape.is_visible,
        });

        return baseAnnotation;
    }, initialAnnotation);
};

export const getAnnotationsFromDTO = (annotations: AnnotationDTO[], projectLabels: Label[]) => {
    if (annotations.length === 0) {
        return [];
    }

    // Todo Ui: group keypoint annotations by "Shape ownership"
    if (annotations.every(isKeypointAnnotationDTO)) {
        return [getKeypointAnnotation(annotations, projectLabels)];
    }

    return annotations.map((annotation, index) => {
        return getAnnotation(annotation, projectLabels, index);
    });
};

const toShapeDTO = (shape: Shape): ShapeDTO => {
    switch (shape.shapeType) {
        case ShapeType.Rect: {
            return {
                type: SHAPE_TYPE_DTO.RECTANGLE,
                x: shape.x,
                y: shape.y,
                width: shape.width,
                height: shape.height,
            };
        }
        case ShapeType.RotatedRect: {
            return {
                type: SHAPE_TYPE_DTO.ROTATED_RECTANGLE,
                angle: shape.angle,
                x: shape.x,
                y: shape.y,
                width: shape.width,
                height: shape.height,
            };
        }
        case ShapeType.Circle: {
            const x = shape.x - shape.r;
            const y = shape.y - shape.r;

            return {
                type: SHAPE_TYPE_DTO.ELLIPSE,
                x,
                y,
                width: shape.r * 2,
                height: shape.r * 2,
            };
        }

        case ShapeType.Polygon: {
            return {
                type: SHAPE_TYPE_DTO.POLYGON,
                points: shape.points,
            };
        }

        // we assume each annotation will have one point
        case ShapeType.Pose: {
            return {
                type: SHAPE_TYPE_DTO.KEYPOINT,
                x: shape.points[0].x,
                y: shape.points[0].y,
                is_visible: shape.points[0].isVisible,
            };
        }
    }
};

export const isKeypointAnnotation = (annotation: Annotation): annotation is KeypointAnnotation => {
    return isPoseShape(annotation.shape);
};

export const getKeypointToAnnotationDTO = (annotation: KeypointAnnotation) => {
    return annotation.shape.points.map((point) => {
        return toAnnotationDTO({
            id: uuidv4(),
            labels: [labelFromUser(point.label)],
            shape: { ...annotation.shape, points: [point] },
            zIndex: 0,
            isSelected: false,
            isHidden: false,
            isLocked: false,
        });
    });
};

// Note the server does not expect to receive the label's source,
// which is why we need to remove it from the AnnotationLabelDTO
type LabelDTOWithoutSource = Omit<AnnotationLabelDTO, 'source'>;
type AnnotationWithoutLabelSourceDTO = Omit<AnnotationDTO, 'labels'> & { labels: LabelDTOWithoutSource[] };

export const toAnnotationDTO = (annotation: Annotation): AnnotationWithoutLabelSourceDTO => {
    const labels = annotation.labels.map((label: AnnotationLabel): LabelDTOWithoutSource => {
        const { id, score, hotkey } = label;

        return {
            id,
            probability: score === undefined ? 1 : score,
            hotkey,
        };
    });

    const shape = toShapeDTO(annotation.shape);

    return {
        id: annotation.id,
        shape,
        labels,
        labels_to_revisit: [],
    };
};

export const getExplanations = (explanations: ExplanationDTO[]): Explanation[] => {
    return explanations.map((explanation: ExplanationDTO) => {
        const { id, name, url, label_id, roi, binary } = explanation;

        return { id, name, url, labelsId: label_id, roi, binary };
    });
};

// If a model is trained with bad data then it may return many annotations
// in this case, to prevent possible performance issues, we want to limit the
// amount of annotations that we show to the user
export const getLimitedPredictedAnnotations = (annotations: Annotation[]): Annotation[] => {
    if (hasMaxAllowedAnnotations(annotations)) {
        // First we remove all annotations that have a low score
        const limitedAnnotations = sortBy(annotations, (annotation) => {
            const scores = annotation.labels.map((label) => (isPrediction(label) ? (label.score ?? 0) : 0));

            return Math.max(...scores);
        }).splice(0, MAX_SUPPORTED_ANNOTATIONS);

        // Next we need to sort the limited annotations back into their original order and reset their
        // zIndex value
        return sortBy(limitedAnnotations, (annotation) => annotation.zIndex).map((annotation, index) => {
            return {
                ...annotation,
                zIndex: index,
            };
        });
    }
    return annotations;
};

export const buildPredictionParams = (mediaItem: MediaItem, datasetIdentifier: DatasetIdentifier): PredictionParams => {
    if (isImage(mediaItem)) {
        return {
            image_id: mediaItem.identifier.imageId,
            dataset_id: datasetIdentifier.datasetId,
        };
    }
    if (isVideo(mediaItem)) {
        return {
            video_id: mediaItem.identifier.videoId,
            dataset_id: datasetIdentifier.datasetId,
        };
    }
    return {
        video_id: mediaItem.identifier.videoId,
        frame_index: mediaItem.identifier.frameNumber.toString(),
        dataset_id: datasetIdentifier.datasetId,
    };
};

// TODO: delete and replace PredictionMode with PredictionCache once FEATURE_FLAG_MODELMESH is removed
export const getPredictionCache = (predictionMode: PredictionMode | string): PredictionCache => {
    switch (predictionMode) {
        case PredictionMode.AUTO:
            return PredictionCache.AUTO;
        case PredictionMode.LATEST:
            return PredictionCache.ALWAYS;
        default:
            return PredictionCache.NEVER;
    }
};
