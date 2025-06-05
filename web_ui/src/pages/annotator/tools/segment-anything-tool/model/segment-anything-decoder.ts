// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as OpenCVTypes from '@geti/smart-tools/opencv-types';
import * as ort from 'onnxruntime-common';

import { isPointInShape } from '../../../../../core/annotations/math';
import { Point } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { PostProcessor } from './post-processing';
import { EncodingOutput } from './segment-anything-encoder';
import { SegmentAnythingResult } from './segment-anything-result';
import { type Session } from './session';

type cv = typeof OpenCVTypes;

type InteractiveAnnotationPoint = Point & { positive: boolean };

export interface SegmentAnythingPrompt {
    image: string | ArrayBuffer | undefined;
    points: InteractiveAnnotationPoint[] | undefined;
    boxes: Point[][] | undefined;
    ouputConfig: { type: ShapeType };
}

export class SegmentAnythingDecoder {
    constructor(
        private cv: cv,
        private session: Session
    ) {}

    public async process(encodingOutput: EncodingOutput, input: SegmentAnythingPrompt): Promise<SegmentAnythingResult> {
        const { masks, iouPredictions } = await this.processDecoder(
            { boxes: input.boxes ?? [], points: input.points ?? [] },
            encodingOutput
        );

        const maskIdx = this.getIndexOfMaskWithHighestConfidence(iouPredictions);

        const size = masks.dims[2] * masks.dims[3];
        const maskOffset = maskIdx * size;
        const pixels = new Uint8ClampedArray(new ArrayBuffer(size));

        for (let y = 0; y < masks.dims[2]; y++) {
            for (let x = 0; x < masks.dims[3]; x++) {
                const value = Number(masks.data[maskOffset + y * masks.dims[3] + x]);

                const idx = y * masks.dims[3] + x;
                pixels[idx] = value > 0 ? 255 : 0;
            }
        }

        const postProcessor = new PostProcessor(this.cv);

        const positivePoints = input.points?.filter(({ positive }) => positive) ?? [];

        const sizes = {
            height: masks.dims[2],
            width: masks.dims[3],
            originalWidth: encodingOutput.originalWidth + 1,
            originalHeight: encodingOutput.originalHeight + 1,
        };

        const results = postProcessor.maskToAnnotationShape(pixels, sizes, {
            ...(input.ouputConfig ?? { type: 'polygon' }),
            shapeFilter: (shape) => positivePoints.some((point) => isPointInShape(shape, point)),
        });
        return results;
    }

    private getIndexOfMaskWithHighestConfidence(iou_predictions: ort.Tensor) {
        let predictionIdx = 0;

        for (let p = 0; p < iou_predictions.dims[1]; p++) {
            if (iou_predictions.data[p] > iou_predictions.data[predictionIdx]) {
                predictionIdx = p;
            }
        }

        return predictionIdx;
    }

    private async processDecoder(
        prompt: {
            points: InteractiveAnnotationPoint[];
            boxes: Point[][];
        },
        { encoderResult, originalWidth, originalHeight, newWidth, newHeight }: EncodingOutput
    ): Promise<{
        masks: ort.Tensor;
        iouPredictions: ort.Tensor;
        lowResMasks: ort.Tensor;
    }> {
        const pointCoords: number[] = [];
        const pointLabels: number[] = [];

        const xRatio = newWidth / originalWidth;
        const yRatio = newHeight / originalHeight;

        for (const point of prompt.points) {
            pointCoords.push(point.x * xRatio);
            pointCoords.push(point.y * yRatio);
            pointLabels.push(point.positive ? 1 : 0);
        }

        if (prompt.boxes.length === 0) {
            pointCoords.push(0);
            pointCoords.push(0);
            pointLabels.push(-1);
        }

        for (const box of prompt.boxes) {
            pointCoords.push(box[0].x * xRatio);
            pointCoords.push(box[0].y * yRatio);
            pointLabels.push(2);
            pointCoords.push(box[1].x * xRatio);
            pointCoords.push(box[1].y * yRatio);
            pointLabels.push(3);
        }

        const ratio = 1024 / Math.max(originalHeight, originalWidth);
        const feeds: Record<string, ort.Tensor> = {
            image_embeddings: encoderResult,
            // TODO: reuse the low_res_masks output, also use existing polygons?
            mask_input: new ort.Tensor(new Float32Array(256 * 256).fill(1), [1, 1, 256, 256]),
            has_mask_input: new ort.Tensor(new Float32Array(1).fill(0), [1]),
            orig_im_size: new ort.Tensor(
                new Float32Array([Math.round(originalHeight * ratio), Math.round(originalWidth * ratio)]),
                [2]
            ),
            point_coords: new ort.Tensor(new Float32Array(pointCoords), [1, pointCoords.length / 2, 2]),
            point_labels: new ort.Tensor(new Float32Array(pointLabels), [1, pointLabels.length]),
        };

        const outputData = await this.session.run(feeds);

        return {
            masks: outputData['masks'],
            iouPredictions: outputData['iou_predictions'],
            lowResMasks: outputData['low_res_masks'],
        };
    }
}
