// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isNil from 'lodash/isNil';
import { v4 as uuidv4 } from 'uuid';

import { getImageDataFromTiffFile } from '../../../../shared/canvas-utils';
import { isTiffFormat, loadImageFromFile } from '../../../../shared/media-utils';
import { Label } from '../../../labels/label.interface';
import { MediaItem } from '../../../media/media.interface';
import { mediaIdentifierToDTO } from '../../../media/services/utils';
import { isVideo, Video } from '../../../media/video.interface';
import { ProjectIdentifier } from '../../../projects/core.interface';
import { DatasetIdentifier } from '../../../projects/dataset.interface';
import { instance as defaultAxiosInstance } from '../../../services/axios-instance';
import { API_URLS } from '../../../services/urls';
import { Annotation, TaskChainInput } from '../../annotation.interface';
import {
    AnnotationDTO,
    ImageIdDTO,
    RectDTO,
    SHAPE_TYPE_DTO,
    ShapeDTO,
    VideoFrameIdDTO,
} from '../../dtos/annotation.interface';
import {
    NewExplanationsDTO,
    NewPredictionsDTO,
    NewTestPredictionsDTO,
    PipelineServerStatusDTO,
} from '../../dtos/prediction.interface';
import { Rect } from '../../shapes.interface';
import { ExplanationResult, InferenceResult, InferenceService } from '../inference-service.interface';
import { InferenceServerStatusResult, PredictionCache, PredictionMode } from '../prediction-service.interface';
import {
    buildPredictionParams,
    getExplanations as convertExplanations,
    convertExplanationsDTO,
    convertLabelToDTO,
    convertPredictionsDTO,
    getAnnotationsFromDTO,
    getLimitedPredictedAnnotations,
    getPredictionCache,
    PREDICTION_TIMEOUT,
} from '../utils';
import { VideoPaginationOptions } from '../video-pagination-options.interface';
import {
    BatchPredictionsDTO,
    convertBatchToRecord,
    convertDtosToAnnotations,
    CreateApiService,
    getExplanationRoi,
    getInputShapeRect,
    hasEmptyLabel,
} from './utils';

const setInputConfig =
    (selectedInput: TaskChainInput) =>
    (predictionAnnotation: AnnotationDTO): AnnotationDTO => {
        const [firstTaskLabel] = selectedInput.labels;
        const shape = { ...getInputShapeRect(selectedInput), type: SHAPE_TYPE_DTO.RECTANGLE } as ShapeDTO;

        return {
            ...predictionAnnotation,
            shape,
            id: selectedInput.id,
            labels: [convertLabelToDTO(firstTaskLabel), ...predictionAnnotation.labels],
        };
    };

const setInputConfigPolygons = (
    predictionAnnotations: AnnotationDTO[],
    selectedInput: TaskChainInput,
    projectLabels: Label[]
): AnnotationDTO[] => {
    const [firstTaskLabel] = selectedInput.labels;
    const [firstPrediction] = predictionAnnotations;
    const roi = { ...getInputShapeRect(selectedInput), type: SHAPE_TYPE_DTO.RECTANGLE } as RectDTO;
    const isEmpty = firstPrediction.labels.some(hasEmptyLabel(projectLabels));

    if (isEmpty) {
        return [setInputConfig(selectedInput)(firstPrediction)];
    }

    return [
        {
            shape: roi,
            id: selectedInput.id,
            labels: [convertLabelToDTO(firstTaskLabel)],
            labels_to_revisit: [],
        },
        ...predictionAnnotations,
    ];
};

const getInputConfig = (predictions: AnnotationDTO[], selectedInput: TaskChainInput, projectLabels: Label[]) => {
    const isAllPolygons = predictions.every(({ shape }) => shape.type === SHAPE_TYPE_DTO.POLYGON);

    return isAllPolygons
        ? setInputConfigPolygons(predictions, selectedInput, projectLabels)
        : predictions.map(setInputConfig(selectedInput));
};

export const createApiInferenceService: CreateApiService<InferenceService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getTestPredictions = async (
        projectIdentifier: ProjectIdentifier,
        labels: Label[],
        testId: string,
        predictionId: string
    ): Promise<InferenceResult> => {
        const { data } = await instance.get<NewTestPredictionsDTO>(
            router.TEST_PREDICTIONS(projectIdentifier, testId, predictionId)
        );

        if (!data) {
            return [];
        }

        return convertDtosToAnnotations(data, data.media_identifier, labels);
    };

    const getPredictions = async (
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItem: MediaItem,
        predictionCache: PredictionCache,
        taskId?: string,
        selectedInput?: TaskChainInput,
        signal?: AbortSignal
    ): Promise<InferenceResult> => {
        if (isVideo(mediaItem)) {
            throw new Error('video is not supported');
        }

        const options =
            predictionCache === PredictionCache.NEVER
                ? { signal }
                : { timeout: PREDICTION_TIMEOUT, timeoutErrorMessage: 'Failed retrieving predictions', signal };

        const { data } = await instance.post<NewPredictionsDTO>(
            router.PREDICTION_NEW(datasetIdentifier, predictionCache, taskId, selectedInput?.shape as Rect),
            buildPredictionParams(mediaItem, datasetIdentifier),
            options
        );

        if (!data) {
            return [];
        }

        const mediaIdentifierDTO = mediaIdentifierToDTO(mediaItem.identifier) as VideoFrameIdDTO | ImageIdDTO;

        const predictionsDTO = convertPredictionsDTO(data, mediaIdentifierDTO);

        const predictionsWithInputConfig = isNil(selectedInput)
            ? predictionsDTO.annotations
            : getInputConfig(predictionsDTO.annotations, selectedInput, projectLabels);

        const formattedPredictions = getAnnotationsFromDTO(predictionsWithInputConfig, projectLabels);

        return getLimitedPredictedAnnotations(formattedPredictions);
    };

    const getExplanations = async (
        datasetIdentifier: DatasetIdentifier,
        mediaItem: MediaItem,
        taskId?: string,
        selectedInput?: TaskChainInput,
        signal?: AbortSignal
    ): Promise<ExplanationResult> => {
        if (isVideo(mediaItem)) {
            throw new Error('video is not supported');
        }

        const { data } = await instance.post<NewExplanationsDTO>(
            router.EXPLAIN_NEW(datasetIdentifier, taskId, selectedInput?.shape as Rect),
            buildPredictionParams(mediaItem, datasetIdentifier),
            { signal }
        );

        if (!data) {
            return [];
        }

        const finalRoi = getExplanationRoi(mediaItem, selectedInput);

        return convertExplanations(convertExplanationsDTO(data, finalRoi));
    };

    const getPredictionsForFile = async (
        projectIdentifier: ProjectIdentifier,
        projectLabels: Label[],
        imageFile: File
    ): Promise<InferenceResult> => {
        const options = new FormData();
        options.set('file', imageFile);

        const { data } = await instance.post<NewPredictionsDTO>(router.PREDICTION_NEW(projectIdentifier), options);

        if (!data) {
            return [];
        }

        const imageIdentifierDTO: ImageIdDTO = {
            image_id: '',
            type: 'image',
        };

        return convertDtosToAnnotations(data, imageIdentifierDTO, projectLabels);
    };

    const getVideoPredictions = async (
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItem: Video,
        mode: PredictionMode,
        options: VideoPaginationOptions = {
            startFrame: 0,
            endFrame: mediaItem.metadata.frames,
            frameSkip: mediaItem.metadata.frameStride,
            labelsOnly: false,
        },
        signal: AbortSignal
    ): Promise<Record<number, Annotation[]>> => {
        const params = {
            dataset_id: datasetIdentifier.datasetId,
            end_frame: options.endFrame.toString(),
            frame_skip: options.frameSkip.toString(),
            start_frame: options.startFrame.toString(),
            video_id: mediaItem.identifier.videoId,
        };

        const response = await instance.post<BatchPredictionsDTO>(
            router.BATCH_PREDICT(datasetIdentifier, getPredictionCache(mode)),
            params,
            { signal }
        );

        const { batch_predictions } = response.data ?? { batch_predictions: [] };

        return convertBatchToRecord(batch_predictions, projectLabels);
    };

    const getVideoPredictionsStream = async (
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItem: Video,
        mode: PredictionMode,
        options: VideoPaginationOptions = {
            startFrame: 0,
            endFrame: mediaItem.metadata.frames,
            frameSkip: mediaItem.metadata.frameStride,
            labelsOnly: false,
        }
    ): Promise<Record<number, Annotation[]>> => {
        const params = {
            dataset_id: datasetIdentifier.datasetId,
            end_frame: options.endFrame.toString(),
            frame_skip: options.frameSkip.toString(),
            start_frame: options.startFrame.toString(),
            video_id: mediaItem.identifier.videoId,
        };

        const { data } = await instance.post<string>(
            router.BATCH_PREDICT_STREAM(datasetIdentifier, getPredictionCache(mode)),
            params,
            { responseType: 'stream' }
        );

        const result = /data:(.*)/.exec(data);
        if (result && result.length === 2) {
            const parsed = JSON.parse(result[1]) as BatchPredictionsDTO;

            return convertBatchToRecord(parsed.batch_predictions, projectLabels);
        }

        return {};
    };

    const getExplanationsForFile = async (
        projectIdentifier: ProjectIdentifier,
        imageFile: File
    ): Promise<ExplanationResult> => {
        const options = new FormData();
        options.set('file', imageFile);

        const { data } = await instance.post<NewExplanationsDTO>(router.EXPLAIN_NEW(projectIdentifier), options);

        if (!data) {
            return [];
        }

        const { width, height } = isTiffFormat(imageFile)
            ? await getImageDataFromTiffFile(imageFile)
            : await loadImageFromFile(imageFile);

        const roi = { id: uuidv4(), x: 0, y: 0, width, height, type: 'RECTANGLE' };

        return convertExplanations(convertExplanationsDTO(data, roi));
    };

    const getInferenceServerStatus = async (
        projectIdentifier: ProjectIdentifier,
        taskId?: string
    ): Promise<InferenceServerStatusResult> => {
        const url = router.PIPELINES_STATUS(projectIdentifier, taskId);
        const response = await instance.get<PipelineServerStatusDTO>(url);

        return { isInferenceServerReady: response.data.pipeline_ready };
    };

    return {
        getPredictions,
        getVideoPredictions,
        getVideoPredictionsStream,
        getExplanations,
        getTestPredictions,
        getPredictionsForFile,
        getExplanationsForFile,
        getInferenceServerStatus,
    };
};
