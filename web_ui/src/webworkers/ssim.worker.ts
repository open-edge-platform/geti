// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// Dependencies get bundled into the worker

import { OpenCVLoader } from '@geti/smart-tools';
import { expose } from 'comlink';
import type OpenCVTypes from 'OpenCVTypes';

import { RegionOfInterest } from '../core/annotations/annotation.interface';
import { Rect } from '../core/annotations/shapes.interface';
import { Vec2 } from '../core/annotations/vec2';
import { MINIMUM_THRESHOLD, RunSSIMProps, SSIMMatch } from '../pages/annotator/tools/ssim-tool/ssim-tool.interface';

declare const self: DedicatedWorkerGlobalScope;

let CV: OpenCVTypes.cv | null = null;

const terminate = (): void => {
    self.close();
};

interface Match {
    value: number;
    x: number;
    y: number;
}

const SSIMScale: Vec2 = { x: 250, y: 250 };

class SSIM {
    buildImage(imageData: ImageData, roi: RegionOfInterest): { image: OpenCVTypes.Mat; scaleFactor: Vec2 } {
        const image = new CV.Mat();
        const originalImage = CV.matFromImageData(imageData);
        const imageSection = originalImage.roi(new CV.Rect(roi.x, roi.y, roi.width, roi.height));
        CV.cvtColor(imageSection, imageSection, CV.COLOR_RGBA2RGB, 0);
        CV.resize(imageSection, image, new CV.Size(SSIMScale.x, SSIMScale.y), 0, 0, CV.INTER_AREA);

        const scaleFactor = { x: SSIMScale.x / imageSection.cols, y: SSIMScale.y / imageSection.rows };
        originalImage.delete();
        imageSection.delete();

        return { image, scaleFactor };
    }

    runSSIM(image: OpenCVTypes.Mat, scaleFactor: Vec2, templateArea: Rect): { probabilityImage: OpenCVTypes.Mat } {
        const mask = new CV.Mat();
        const probabilityImage = new CV.Mat();
        const template = image.roi(
            new CV.Rect(
                templateArea.x * scaleFactor.x,
                templateArea.y * scaleFactor.y,
                templateArea.width * scaleFactor.x,
                templateArea.height * scaleFactor.y
            )
        );
        CV.matchTemplate(image, template, probabilityImage, CV.TM_CCORR_NORMED, mask);
        CV.normalize(probabilityImage, probabilityImage, 0, 1, CV.NORM_MINMAX, CV.CV_64FC1);
        mask.delete();
        template.delete();
        return { probabilityImage };
    }

    getMatches(
        probabilityImage: OpenCVTypes.Mat,
        scaleFactor: Vec2,
        templateArea: Rect,
        roi: RegionOfInterest
    ): SSIMMatch[] {
        const items: Match[] = [];
        const offset = { x: 0.5, y: 0.5 };
        for (let y = 0; y < probabilityImage.rows; y++) {
            for (let x = 0; x < probabilityImage.cols; x++) {
                const value = probabilityImage.doubleAt(y, x);
                if (value > MINIMUM_THRESHOLD) {
                    items.push({
                        x: (x + offset.x) / scaleFactor.x,
                        y: (y + offset.y) / scaleFactor.y,
                        value,
                    });
                }
            }
        }

        items.sort((a, b) => b.value - a.value);
        return items.map((match: Match) => {
            return {
                shape: { ...templateArea, x: match.x + roi.x, y: match.y + roi.y },
                confidence: match.value,
            };
        });
    }

    executeSSIM({ imageData, template, roi }: RunSSIMProps): SSIMMatch[] {
        let image, scaleFactor, probabilityImage;
        let results: SSIMMatch[] = [];
        try {
            ({ image, scaleFactor } = this.buildImage(imageData, roi));
            ({ probabilityImage } = this.runSSIM(image, scaleFactor, template));
            results = this.getMatches(probabilityImage, scaleFactor, template, roi);
        } catch (error) {
            console.warn('Something went wrong while trying to execute SSIM.\n Error: ', error);
        } finally {
            image?.delete();
            probabilityImage?.delete();
        }

        return results;
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

const WorkerApi = { SSIM, terminate, waitForOpenCV };

expose(WorkerApi);
