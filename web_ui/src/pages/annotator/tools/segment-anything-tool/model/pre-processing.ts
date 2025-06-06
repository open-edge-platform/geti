// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as ort from 'onnxruntime-web';
import type cv from 'OpenCVTypes';

interface PreprocessorResult {
    tensor: ort.Tensor;
    width: number;
    height: number;
    newWidth: number;
    newHeight: number;
}

export interface OpenCVPreprocessorConfig {
    normalize: {
        enabled: boolean;
        mean?: number[];
        std?: number[];
    };
    resize: boolean;
    size: number;
    squareImage: boolean;
    pad: boolean;
    padSize: number;
}

export class OpenCVPreprocessor {
    config: OpenCVPreprocessorConfig;

    constructor(
        private cv: cv,
        config: OpenCVPreprocessorConfig
    ) {
        this.config = config;
    }

    public process(initialImageData: ImageData): PreprocessorResult {
        const imageCv = this.loadImage(initialImageData);

        const preProcessedImage: cv.Mat = imageCv.clone();
        let input: cv.Mat | null = null;
        try {
            const { width, height, newWidth, newHeight } = this.resizeImage(preProcessedImage);

            // Apply color space transformations
            preProcessedImage.convertTo(preProcessedImage, this.cv.CV_32F, 1 / 255);
            this.processImage(preProcessedImage);

            input = this.cv.blobFromImage(preProcessedImage);
            if (!input) {
                throw new Error('Something went wrong with preprocessing the image.');
            }

            const tensor = new ort.Tensor('float32', input.data32F, [1, 3, this.config.size, this.config.size]);
            return { tensor, width, height, newWidth, newHeight };
        } finally {
            imageCv.delete();
            preProcessedImage?.delete();
            input?.delete();
        }
    }

    private loadImage(imageData: ImageData): cv.Mat {
        // TODO: check if it is faster / more appropriate if we traser this value
        // https://github.com/GoogleChromeLabs/comlink#comlinktransfervalue-transferables-and-comlinkproxyvalue
        const src = this.cv.matFromImageData(imageData);
        // This is important as otherwise the matrix has too many channels
        // and we don't want to convert the alpha channel to the ort tesnsor
        this.cv.cvtColor(src, src, this.cv.COLOR_RGBA2RGB, 0);

        return src;
    }

    private resizeImage(preProcessedImage: cv.Mat) {
        const width = this.config.pad ? this.config.padSize : preProcessedImage.cols;
        const height = this.config.pad ? this.config.padSize : preProcessedImage.rows;

        if (this.config.resize) {
            const CV_INTERPOLATION = this.cv.INTER_LANCZOS4;
            if (!this.config.squareImage) {
                if (preProcessedImage.cols > preProcessedImage.rows) {
                    const scale = this.config.size / preProcessedImage.cols;
                    const h = Math.ceil(preProcessedImage.rows * scale);
                    const w = this.config.size;
                    this.cv.resize(
                        preProcessedImage,
                        preProcessedImage,
                        new this.cv.Size(w, h),
                        0,
                        0,
                        CV_INTERPOLATION
                    );
                } else {
                    const scale = this.config.size / preProcessedImage.rows;
                    const h = this.config.size;
                    const w = Math.ceil(preProcessedImage.cols * scale);
                    this.cv.resize(
                        preProcessedImage,
                        preProcessedImage,
                        new this.cv.Size(w, h),
                        0,
                        0,
                        CV_INTERPOLATION
                    );
                }
            } else {
                this.cv.resize(
                    preProcessedImage,
                    preProcessedImage,
                    new this.cv.Size(this.config.size, this.config.size),
                    0,
                    0,
                    CV_INTERPOLATION
                );
            }
        }

        const newWidth = preProcessedImage.cols;
        const newHeight = preProcessedImage.rows;

        if (this.config.pad) {
            this.cv.copyMakeBorder(
                preProcessedImage,
                preProcessedImage,
                0,
                height - preProcessedImage.rows,
                0,
                width - preProcessedImage.cols,
                this.cv.BORDER_CONSTANT,
                new this.cv.Scalar(0, 0, 0, 0)
            );
        }

        return {
            width,
            height,
            newWidth,
            newHeight,
        };
    }

    private processImage(dst: cv.Mat): void {
        // RITM requires the image to normalized. RITM code uses theses hardcoded values for some reason.
        let norm: cv.Mat | null = null;
        let stdDev: cv.Mat | null = null;
        try {
            if (this.config.normalize.mean) {
                const normValue = new this.cv.Scalar(
                    this.config.normalize.mean[0],
                    this.config.normalize.mean[1],
                    this.config.normalize.mean[2]
                );
                norm = dst.clone();
                norm.setTo(normValue);

                this.cv.subtract(dst, norm, dst);
            }

            if (this.config.normalize.std) {
                const stdDevValues = new this.cv.Scalar(
                    this.config.normalize.std[0],
                    this.config.normalize.std[1],
                    this.config.normalize.std[2]
                );
                stdDev = dst.clone();
                stdDev.setTo(stdDevValues);

                this.cv.divide(dst, stdDev, dst, 1);
            }
        } finally {
            stdDev?.delete();
            norm?.delete();
        }
    }
}
