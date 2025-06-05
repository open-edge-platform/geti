// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// Dependencies get bundled into the worker

import { OpenCVLoader } from '@geti/smart-tools';
import * as OpenCVTypes from '@geti/smart-tools/opencv-types';
import { expose } from 'comlink';

import { Point } from '../core/annotations/shapes.interface';
import { Marker } from '../pages/annotator/tools/marker-tool/marker-tool.interface';
import { WatershedPolygon } from '../pages/annotator/tools/watershed-tool/watershed-tool.interface';
import { approximateShape, formatContourToPoints } from './utils';

declare const self: DedicatedWorkerGlobalScope;

let CV: OpenCVTypes.cv | null = null;

const terminate = (): void => {
    self.close();
};

const waitForOpenCV = async (): Promise<boolean> => {
    if (CV) {
        return true;
    } else {
        return OpenCVLoader(self).then((cvInstance: OpenCVTypes.cv) => {
            CV = cvInstance;

            return true;
        });
    }
};

class Watershed {
    imageData: OpenCVTypes.Mat;
    mask: OpenCVTypes.Mat;
    originalHeight: number;
    originalWidth: number;
    originalImage: OpenCVTypes.Mat;

    constructor(imageData: ImageData) {
        this.originalImage = CV.matFromImageData(imageData);

        // Convert image colors
        CV.cvtColor(this.originalImage, this.originalImage, CV.COLOR_RGBA2RGB, 0);

        this.imageData = this.originalImage.clone();

        this.originalHeight = this.originalImage.rows;
        this.originalWidth = this.originalImage.cols;

        // Create a mask
        this.mask = new CV.Mat();
    }

    drawMarkers(markers: Marker[]): void {
        this.mask?.delete();

        this.mask = new CV.Mat(this.imageData.rows, this.imageData.cols, CV.CV_32S, new CV.Scalar(0));

        markers.forEach((marker) => {
            const line = new CV.Mat(marker.points.length, 1, CV.CV_32SC2);

            // Convert all lines into a matrix
            // [A x x x x x]     A = marker[markerIndex].points[0].x
            // [B y y y y y]     B = marker[markerIndex].points[0].y
            marker.points.forEach(({ x, y }, idx) => {
                line.intPtr(idx, 0)[0] = (x / this.originalWidth) * this.mask.cols;
                line.intPtr(idx, 0)[1] = (y / this.originalHeight) * this.mask.rows;
            });

            const markersVector = new CV.MatVector();

            markersVector.push_back(line);

            CV.polylines(this.mask, markersVector, false, new CV.Scalar(marker.id), 4);

            line.delete();
            markersVector.delete();
        });
    }

    getPolygons(markers: Marker[]): WatershedPolygon[] {
        const polygons: WatershedPolygon[] = [];

        for (let markerIndex = 0; markerIndex < markers.length; markerIndex++) {
            let shapeMat: OpenCVTypes.Mat | null = null;
            const contours: OpenCVTypes.MatVector = new CV.MatVector();
            const hierachy: OpenCVTypes.Mat = new CV.Mat();

            try {
                const markerPolygon = polygons.find((polygon) => polygon.id === markers[markerIndex].id);

                // Discard the background marker and duplicate polygons
                if (markerPolygon || markers[markerIndex].id === 1) {
                    continue;
                }

                shapeMat = this.mask.clone();

                shapeMat.convertTo(shapeMat, CV.CV_8U);

                CV.threshold(shapeMat, shapeMat, markers[markerIndex].id - 1, 0, CV.THRESH_TOZERO);
                CV.threshold(shapeMat, shapeMat, markers[markerIndex].id, 0, CV.THRESH_TOZERO_INV);

                CV.findContours(shapeMat, contours, hierachy, CV.RETR_CCOMP, CV.CHAIN_APPROX_NONE);

                for (let idx = 0; idx < contours.size(); idx++) {
                    const optimizedContours = approximateShape(CV, contours.get(idx));
                    const points: Point[] = formatContourToPoints(
                        this.mask,
                        optimizedContours,
                        this.originalWidth,
                        this.originalHeight
                    );
                    optimizedContours?.delete();
                    polygons.push({ id: markers[markerIndex].id, label: markers[markerIndex].label, points });
                }
            } catch (error) {
                console.warn('Something went wrong while trying to execute getPolygons.\n Error: ', error);
            } finally {
                // Cleanup
                shapeMat?.delete();
                contours?.delete();
                hierachy?.delete();
            }
        }

        return polygons;
    }

    scaleImage(sensitivity: number): void {
        const scale = Math.max(this.originalImage.cols, this.originalImage.rows) / sensitivity;
        const size = new CV.Size(this.originalImage.cols / scale, this.originalImage.rows / scale);
        const hasSameSize = size.width === this.imageData.cols && size.height === this.imageData.rows;

        if (hasSameSize) {
            return;
        }

        if (scale > 1) {
            CV.resize(this.originalImage, this.imageData, size, 0, 0, CV.INTER_AREA);
        } else {
            // Delete previous imageData
            this.imageData?.delete();
            this.imageData = this.originalImage.clone();
        }
    }

    clearMemory(): void {
        try {
            this.imageData?.delete();
            this.originalImage?.delete();
            this.mask?.delete();
        } catch (error) {
            console.warn('Unable to clear memory.\n Error: ', error);
        }
    }

    executeWatershed(markers: Marker[], sensitivity: number): WatershedPolygon[] {
        let polygons: WatershedPolygon[] = [];

        try {
            // Create a new scaled image based on the sensitivity input
            this.scaleImage(sensitivity);

            // Draw markers
            this.drawMarkers(markers);

            // Run watershed
            CV.watershed(this.imageData, this.mask);

            // Get the resulting polygons
            polygons = this.getPolygons(markers);
        } catch (error) {
            console.warn('Something went wrong while trying to execute Watershed.\n Error: ', error);
        }

        return polygons;
    }
}

const WorkerApi = { Watershed, terminate, waitForOpenCV };

expose(WorkerApi);
