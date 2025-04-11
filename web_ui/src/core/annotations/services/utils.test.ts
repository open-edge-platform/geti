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

import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import {
    getMockedImageMediaItem,
    getMockedVideoFrameMediaItem,
    getMockedVideoMediaItem,
} from '../../../test-utils/mocked-items-factory/mocked-media';
import { Label } from '../../labels/label.interface';
import { AnnotationDTO, KeypointDTO, SHAPE_TYPE_DTO, ShapeDTO } from '../dtos/annotation.interface';
import { PredictionCache, PredictionMode } from './prediction-service.interface';
import {
    buildPredictionParams,
    convertExplanationsDTO,
    convertLabelToDTO,
    convertPredictionLabelDTO,
    getAnnotation,
    getAnnotationsFromDTO,
    getExplanations,
    getKeypointAnnotation,
    getPredictionCache,
} from './utils';

describe('annotation service utils', () => {
    it('convertPredictionLabelDTO', () => {
        const data = { id: '123', name: 'test', probability: 0.1 };
        expect(convertPredictionLabelDTO(data)).toEqual({
            id: data.id,
            probability: data.probability,
            source: {
                model_id: 'latest',
                user_id: null,
                model_storage_id: 'storage_id',
            },
        });
    });

    it("removes labels that are not present in the project's labels", () => {
        const projectLabels: Label[] = [getMockedLabel({ id: 'existing-label', name: 'existing label' })];

        const annotationDTO: AnnotationDTO = {
            id: 'test',
            labels: [
                // One label that exists in the project
                {
                    id: projectLabels[0].id,
                    hotkey: '',
                    probability: 1.0,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
                // Another one that does not exist in the project
                {
                    id: 'non-existent-label',
                    hotkey: '',
                    probability: 1.0,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
            shape: { type: SHAPE_TYPE_DTO.RECTANGLE, x: 0, y: 0, width: 1.0, height: 1.0 },
            labels_to_revisit: [],
        };

        const annotation = getAnnotation(annotationDTO, projectLabels, 0);

        expect(annotation.labels).toHaveLength(1);
    });

    it('getExplanations', () => {
        const explanation = {
            id: 'id-test',
            url: 'url-test',
            name: 'name-test',
            label_id: 'label-id-test',
            roi: {
                id: 'roi-id',
                shape: {
                    y: 0,
                    x: 0,
                    type: 'rect',
                    width: 10,
                    height: 10,
                },
            },
        };
        expect(getExplanations([explanation])).toEqual([
            {
                binary: undefined,
                id: explanation.id,
                labelsId: explanation.label_id,
                name: explanation.name,
                roi: explanation.roi,
                url: explanation.url,
            },
        ]);
    });

    it('convertLabelToDTO', () => {
        const annotationLabel = {
            score: 1,
            source: { modelId: '1234', modelStorageId: undefined },
            ...getMockedLabel({}),
        };

        expect(convertLabelToDTO(annotationLabel)).toEqual({
            id: annotationLabel.id,
            probability: annotationLabel.score,
            source: {
                user_id: null,
                model_storage_id: null,
                model_id: annotationLabel.source.modelId,
            },
        });
    });

    it('convertExplanationsDTO', () => {
        const roiShape = { id: 'roi-id', x: 10, y: 10, width: 50, height: 50 };
        const config = {
            label_id: 'label-id',
            label_name: 'label-name',
            data: 'data-test',
        };

        const { id: roiId, ...roiConfig } = roiShape;

        expect(convertExplanationsDTO({ created: 'test-date', maps: [config] }, roiShape)).toEqual([
            {
                id: expect.any(String),
                url: '',
                name: config.label_name,
                binary: config.data,
                label_id: config.label_id,
                roi: {
                    id: roiId,
                    shape: { type: '1', ...roiConfig },
                },
            },
        ]);
    });

    describe('buildPredictionParams', () => {
        const datasetIdentifier = {
            workspaceId: 'workspace-id',
            projectId: 'project-id',
            datasetId: 'dataset-id',
            organizationId: 'organization-id',
        };

        it('image', () => {
            const mockedImageMedia = getMockedImageMediaItem({});
            expect(buildPredictionParams(mockedImageMedia, datasetIdentifier)).toEqual({
                dataset_id: datasetIdentifier.datasetId,
                image_id: mockedImageMedia.identifier.imageId,
            });
        });

        it('video', () => {
            const mockedImageMedia = getMockedVideoMediaItem({});
            expect(buildPredictionParams(mockedImageMedia, datasetIdentifier)).toEqual({
                dataset_id: datasetIdentifier.datasetId,
                video_id: mockedImageMedia.identifier.videoId,
            });
        });

        it('video frame', () => {
            const mockedImageMedia = getMockedVideoFrameMediaItem({});
            expect(buildPredictionParams(mockedImageMedia, datasetIdentifier)).toEqual({
                dataset_id: datasetIdentifier.datasetId,
                video_id: mockedImageMedia.identifier.videoId,
                frame_index: String(mockedImageMedia.identifier.frameNumber),
            });
        });
    });

    it('getPredictionCache', () => {
        expect(getPredictionCache(PredictionMode.AUTO)).toEqual(PredictionCache.AUTO);
        expect(getPredictionCache(PredictionMode.ONLINE)).toEqual(PredictionCache.NEVER);
        expect(getPredictionCache(PredictionMode.LATEST)).toEqual(PredictionCache.ALWAYS);
    });

    describe('getKeypointAnnotation', () => {
        const projectLabels: Label[] = [
            getMockedLabel({ id: 'existing-label-1', name: 'existing label 1' }),
            getMockedLabel({ id: 'existing-label-2', name: 'existing label 2' }),
        ];

        const getAnnotationDTO = (shape: KeypointDTO, labelId: string) => ({
            id: 'test-1',
            shape,
            labels_to_revisit: [],
            labels: [
                {
                    id: labelId,
                    hotkey: '',
                    probability: 1.0,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
        });

        it('the new annotation is created with the label of the first point', () => {
            const [label1, label2] = projectLabels;
            const annotationsDTO = [
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.KEYPOINT, x: 0, y: 0, is_visible: true }, label1.id),
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.KEYPOINT, x: 10, y: 10, is_visible: false }, label2.id),
            ];

            const newAnnotation = getKeypointAnnotation(annotationsDTO, projectLabels);

            expect(newAnnotation.labels[0].id).toEqual(label1.id);
            expect(newAnnotation.shape.points[0].label.id).toEqual(label1.id);
        });

        it('bundle multiple annotationsDTO into a single annotation containing multiple points', () => {
            const [label1, label2] = projectLabels;
            const annotationsDTO = [
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.KEYPOINT, x: 0, y: 0, is_visible: true }, label1.id),
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.KEYPOINT, x: 10, y: 10, is_visible: false }, label2.id),
            ];

            const newAnnotation = getKeypointAnnotation(annotationsDTO, projectLabels);

            expect(newAnnotation.shape.points).toHaveLength(annotationsDTO.length);

            annotationsDTO.forEach((annotationDTO, index) => {
                expect(newAnnotation.shape.points[index]).toEqual({
                    x: annotationDTO.shape.x,
                    y: annotationDTO.shape.y,
                    isVisible: annotationDTO.shape.is_visible,
                    label: expect.objectContaining({
                        id: annotationDTO.labels[0].id,
                    }),
                });
            });
        });
    });

    describe('getAnnotationsFromDTO', () => {
        const projectLabel = getMockedLabel({ id: 'existing-label-1', name: 'existing label 1' });

        const getAnnotationDTO = (shape: ShapeDTO, labelId: string) => ({
            id: 'test-1',
            shape,
            labels_to_revisit: [],
            labels: [
                {
                    id: labelId,
                    hotkey: '',
                    probability: 1.0,
                    source: { user_id: 'default_user', model_id: null, model_storage_id: null },
                },
            ],
        });

        it('empty data', () => {
            expect(getAnnotationsFromDTO([], [projectLabel])).toHaveLength(0);
        });

        it('multiple annotation entries with keypoint shape return a single annotation', () => {
            const annotationsDTO = [
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.KEYPOINT, x: 0, y: 0, is_visible: true }, projectLabel.id),
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.KEYPOINT, x: 10, y: 10, is_visible: false }, projectLabel.id),
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.KEYPOINT, x: 30, y: 30, is_visible: false }, projectLabel.id),
            ];

            expect(getAnnotationsFromDTO(annotationsDTO, [projectLabel])).toHaveLength(1);
        });

        it('multiple annotation entries with other shape types return multiple annotations', () => {
            const annotationsDTO = [
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.POLYGON, points: [] }, projectLabel.id),
                getAnnotationDTO(
                    { type: SHAPE_TYPE_DTO.RECTANGLE, x: 10, y: 10, height: 1, width: 1 },
                    projectLabel.id
                ),
                getAnnotationDTO({ type: SHAPE_TYPE_DTO.ELLIPSE, x: 30, y: 30, height: 1, width: 1 }, projectLabel.id),
            ];

            expect(getAnnotationsFromDTO(annotationsDTO, [projectLabel])).toHaveLength(annotationsDTO.length);
        });
    });
});
