// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// Dependencies get bundled into the worker

import { OpenCVLoader } from '@geti/smart-tools';
import { expose } from 'comlink';
import ndarray from 'ndarray';
import ops from 'ndarray-ops';
import * as ort from 'onnxruntime-web';
import type OpenCVTypes from 'OpenCVTypes';

import { RegionOfInterest } from '../core/annotations/annotation.interface';
import { Point, Shape } from '../core/annotations/shapes.interface';
import { ShapeType } from '../core/annotations/shapetype.enum';
import {
    RITMContour,
    RITMMethods,
    RITMPoint,
    TEMPLATE_SIZE,
} from '../pages/annotator/tools/ritm-tool/ritm-tool.interface';
import { isPolygonValid } from '../pages/annotator/tools/utils';
import { sessionParams } from '../pages/annotator/tools/wasm-utils';
import { approximateShape, concatFloat32Arrays, loadSource, stackPlanes } from './utils';

declare const self: DedicatedWorkerGlobalScope;

let CV: OpenCVTypes.cv | null = null;

const terminate = (): void => {
    self.close();
};

interface MainModelResponse {
    instances: ort.Tensor;
    instances_aux: ort.Tensor;
    feature: ort.Tensor;
}

interface Models {
    preprocess: ort.InferenceSession;
    main: ort.InferenceSession;
}

class RITM implements RITMMethods {
    models: Models | undefined;
    image: OpenCVTypes.Mat | undefined;
    mask: OpenCVTypes.Mat | undefined;

    async load() {
        ort.env.wasm.wasmPaths = sessionParams.wasmRoot;
        this.models = {
            main: await this.loadModel(new URL('./ritm/main.onnx', import.meta.url).toString()),
            preprocess: await this.loadModel(new URL('./ritm/preprocess.onnx', import.meta.url).toString()),
        };
    }

    async loadModel(source: string): Promise<ort.InferenceSession> {
        const data = await (await loadSource(source))?.arrayBuffer();

        if (!data) {
            throw 'Could not load model';
        }

        return ort.InferenceSession.create(data);
    }

    loadImage(imageData: ImageData) {
        let imageRGBA: OpenCVTypes.Mat | null = null;
        try {
            imageRGBA = CV.matFromImageData(imageData);
            if (this.image === undefined) {
                this.image = new CV.Mat();
            }

            CV.cvtColor(imageRGBA, this.image, CV.COLOR_RGBA2RGB);

            if (this.mask !== undefined) {
                this.mask.delete();
            }

            this.mask = new CV.Mat.zeros(imageData.height, imageData.width, CV.CV_32FC1);
        } finally {
            imageRGBA?.delete();
        }
    }

    reset() {
        if (this.mask) {
            this.mask.delete();

            if (this.image) {
                this.mask = new CV.Mat.zeros(this.image.rows, this.image.cols, CV.CV_32FC1);
            }
        }
    }

    cleanMemory() {
        this.image?.delete();
        this.mask?.delete();
    }

    async execute(
        imageArea: RegionOfInterest,
        points: RITMPoint[],
        outputShape: ShapeType
    ): Promise<Shape | undefined> {
        if (!this.mask || !this.image) {
            throw 'Cannot execute RITM yet';
        }

        let areaMask: OpenCVTypes.Mat | null = null;
        let resultMask: OpenCVTypes.Mat | null = null;

        try {
            const templateSize = new CV.Size(TEMPLATE_SIZE, TEMPLATE_SIZE);
            const box = new CV.Rect(imageArea.x, imageArea.y, imageArea.width, imageArea.height);
            const imageTensor = this.buildImageTensor(box, templateSize);
            const pointTensor = this.buildPointTensor(box, points, templateSize);
            const coordFeaturesTensor = await this.runPreProcess(pointTensor);
            const modelResult = await this.runMainModel(coordFeaturesTensor, imageTensor);

            resultMask = this.buildResultMask(modelResult.instances, box);
            areaMask = this.mask.roi(box);
            resultMask.copyTo(areaMask);
        } catch (exception) {
            console.warn('error in opencv');
            console.warn(CV.exceptionFromPtr(exception));
        } finally {
            areaMask?.delete();
            resultMask?.delete();

            const contour = this.buildContour(imageArea, points);
            return this.buildOutputShape(contour, outputShape);
        }
    }

    buildOutputShape(contour: RITMContour | undefined, outputShape: ShapeType): Shape | undefined {
        if (contour === undefined) {
            return undefined;
        }

        switch (outputShape) {
            case ShapeType.Polygon:
                const shape: Shape = { shapeType: ShapeType.Polygon, points: contour.contour };
                if (isPolygonValid(shape)) {
                    return shape;
                }
                return undefined;
            case ShapeType.RotatedRect:
                const { x, y } = contour.minAreaRect.center;
                const { width, height } = contour.minAreaRect.size;
                const angle = contour.minAreaRect.angle;

                return { shapeType: ShapeType.RotatedRect, x, y, width, height, angle };
        }
        throw 'Not implemented shape.';
    }

    buildContour(imageArea: RegionOfInterest, points: RITMPoint[]): RITMContour | undefined {
        if (!this.mask) {
            throw 'Cannot buildContour without pointmask';
        }
        if (!this.image) {
            throw 'Cannot buildContour without image';
        }
        const isClose = true;

        const contours = new CV.MatVector();
        const contourArea = this.mask.roi(imageArea);
        const hierarchy = new CV.Mat();
        const contourMask = new CV.Mat();
        let resultContour: RITMContour | undefined = undefined;
        try {
            contourArea.convertTo(contourMask, CV.CV_8UC1, 255);
            CV.threshold(contourMask, contourMask, 120, 250, CV.THRESH_BINARY);
            CV.findContours(contourMask, contours, hierarchy, CV.RETR_EXTERNAL, CV.CHAIN_APPROX_SIMPLE);
            for (let i = 0; i < contours.size(); ++i) {
                const rawContour = contours.get(i);
                const contour = approximateShape(CV, rawContour, isClose);
                const score = points.reduce((collector, { x, y, positive }) => {
                    const pointScore = CV.pointPolygonTest(
                        contour,
                        new CV.Point(x - imageArea.x, y - imageArea.y),
                        false
                    );
                    return collector + pointScore * (positive ? 5 : -1);
                }, 0);
                const area = CV.contourArea(contour);
                if (
                    !resultContour ||
                    score > resultContour.score ||
                    (score === resultContour.score && area > resultContour.area)
                ) {
                    const contourPoints: Point[] = [];
                    for (let row = 0; row < contour.rows; row++) {
                        contourPoints.push({
                            x: (contour.intAt(row, 0) / contourMask.cols) * imageArea.width + imageArea.x,
                            y: (contour.intAt(row, 1) / contourMask.rows) * imageArea.height + imageArea.y,
                        });
                    }
                    const minAreaRect = CV.minAreaRect(contour);
                    minAreaRect.center.x += imageArea.x;
                    minAreaRect.center.y += imageArea.y;
                    resultContour = {
                        contour: contourPoints,
                        area,
                        score,
                        minAreaRect,
                    };
                }
                rawContour.delete();
                contour.delete();
            }
        } finally {
            contourMask?.delete();
            hierarchy?.delete();
            contours?.delete();
            contourArea?.delete();
        }

        return resultContour;
    }

    buildResultMask(mask: ort.Tensor, box: OpenCVTypes.Rect): OpenCVTypes.Mat {
        let normalMat: OpenCVTypes.Mat | null = null;
        try {
            this.sigmoid(mask);
            const maskSize = new CV.Size(mask.dims[3], mask.dims[2]);
            const arraySize = maskSize.width * maskSize.height;
            const normal = mask.data.slice(0, arraySize);
            normalMat = CV.matFromArray(maskSize.height, maskSize.width, CV.CV_32FC1, normal);
            const result = new CV.Mat();
            CV.resize(normalMat, result, new CV.Size(box.width, box.height));
            return result;
        } finally {
            normalMat?.delete();
        }
    }

    buildPointTensor(box: OpenCVTypes.Rect, points: RITMPoint[], templateSize: OpenCVTypes.Size) {
        if (!this.mask) {
            throw 'Cannot build point tensor without pointmask';
        }
        let normal: [OpenCVTypes.Mat, OpenCVTypes.Mat, OpenCVTypes.Mat] | null = null;
        try {
            normal = [
                this.mask.roi(box),
                new CV.Mat.zeros(templateSize.height, templateSize.width, CV.CV_32FC1),
                new CV.Mat.zeros(templateSize.height, templateSize.width, CV.CV_32FC1),
            ];
            CV.resize(normal[0], normal[0], templateSize);

            const scaleTransform = {
                x: box.width / templateSize.width,
                y: box.height / templateSize.height,
            };

            const positiveMask = normal[1]; // Take ref
            const negativeMask = normal[2]; // Take ref

            points.forEach(({ x, y, positive }) => {
                const mask = positive ? positiveMask : negativeMask;
                CV.circle(
                    mask,
                    new CV.Point((x - box.x) / scaleTransform.x, (y - box.y) / scaleTransform.y),
                    5,
                    new CV.Scalar(1),
                    CV.FILLED
                );
            });
            const data = concatFloat32Arrays(normal.map((m) => m.data32F));

            const shape = [1, 3, templateSize.height, templateSize.width];
            return new ort.Tensor('float32', data, shape);
        } finally {
            normal?.forEach((m) => m.delete());
        }
    }

    buildImageTensor(box: OpenCVTypes.Rect, templateSize: OpenCVTypes.Size): ort.Tensor {
        if (!this.image) {
            throw 'buildImageTensor requires imageData to be loaded';
        }

        let dst: OpenCVTypes.Mat | null = null;
        try {
            dst = this.image.roi(box);
            dst.convertTo(dst, CV.CV_32F, 1 / 255);
            CV.resize(dst, dst, templateSize);
            this.processImage(dst);

            const shape = [1, 3, templateSize.height, templateSize.width];
            const data = stackPlanes(CV, dst);
            return new ort.Tensor('float32', data, shape);
        } finally {
            dst?.delete();
        }
    }

    processImage(mat: OpenCVTypes.Mat): void {
        // RITM requires the image to normalized. RITM code uses theses hardcoded values for some reason.
        let norm: OpenCVTypes.Mat | null = null;
        let stdDev: OpenCVTypes.Mat | null = null;
        try {
            const normValue = new CV.Scalar(0.485, 0.456, 0.406);
            norm = mat.clone();
            norm.setTo(normValue);

            const stdDevValues = new CV.Scalar(0.229, 0.224, 0.225);
            stdDev = mat.clone();
            stdDev.setTo(stdDevValues);

            CV.subtract(mat, norm, mat);
            CV.divide(mat, stdDev, mat, 1);
        } finally {
            stdDev?.delete();
            norm?.delete();
        }
    }

    resetPointMask() {
        if (this.mask) {
            this.mask?.delete();

            if (this.image) {
                this.mask = new CV.Mat.zeros(this.image.rows, this.image.cols, CV.CV_32FC1);
            }
        }
    }

    async runPreProcess(pointTensor: ort.Tensor): Promise<ort.Tensor> {
        if (!this.models) {
            throw 'RITM Model needs to be loaded before running preprocess';
        }
        return (await this.models.preprocess.run({ points: pointTensor })).coord_features;
    }

    async runMainModel(points: ort.Tensor, image: ort.Tensor): Promise<MainModelResponse> {
        if (!this.models) {
            throw 'RITM Model needs to be loaded before running HRNet';
        }
        const tensors = { image, points };
        return this.models.main.run(tensors) as unknown as Promise<MainModelResponse>;
    }

    sigmoid(mask: ort.Tensor) {
        const data = ndarray(mask.data as Float32Array, [...mask.dims]);
        const ones = ndarray(new Float32Array(mask.data.length), [...mask.dims]);
        ops.assigns(ones, 1);
        ops.mulseq(data, -1);
        ops.expeq(data);
        ops.addseq(data, 1);
        ops.div(data, ones, data);
    }
}

const waitForOpenCV = async (): Promise<boolean> => {
    if (CV) {
        return true;
    } else {
        return OpenCVLoader().then((cvInstance: OpenCVTypes.cv) => {
            CV = cvInstance;

            return true;
        });
    }
};

const WorkerApi = { RITM, terminate, waitForOpenCV };

expose(WorkerApi);
