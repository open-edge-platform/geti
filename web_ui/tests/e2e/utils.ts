// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import fs from 'fs';

import { resolveDatasetPath } from '../utils/dataset';

interface FishAnnotationFromFile {
    id: string;
    shape: { x: number; y: number; width: number; height: number };
    labels: string[];
}

export type VideoAnnotations = Record<string, FishAnnotationFromFile[][]>;

const FISH_DATASET_PATH = 'cartoon-fish/';

interface CardAnnotationFromFile {
    name: string;
    annotations: Array<{
        shape: { x: number; y: number; width: number; height: number };
        labels: string[];
    }>;
    // These points were recorded clicks when using SAM to annotate each card,
    // thus they can be used to automatically annotate the cards using SAM
    points: Array<{ x: number; y: number; postitive: boolean }>;
}
const CARDS_DATASET_PATH = 'cards/';

export const canAnnotateFishDataset = () => {
    return !fs.existsSync(resolveDatasetPath(FISH_DATASET_PATH));
};

export const loadFishAnnotations = (filename: string, buffer: VideoAnnotations) => {
    const annotationsPath = resolveDatasetPath(FISH_DATASET_PATH, `${filename}.json`);

    if (!buffer[filename]) {
        buffer[filename] = JSON.parse(
            fs.readFileSync(annotationsPath) as unknown as string
        ) as VideoAnnotations[string];
    }

    return buffer[filename];
};

export const loadCardAnnotations = () => {
    const annotationsPath = resolveDatasetPath(CARDS_DATASET_PATH, `cards.json`);

    const cards = JSON.parse(fs.readFileSync(annotationsPath) as unknown as string) as CardAnnotationFromFile[];

    return cards;
};

export const getFishVideoFiles = () => {
    return [
        resolveDatasetPath(`${FISH_DATASET_PATH}/fish_0_60.mp4`),
        resolveDatasetPath(`${FISH_DATASET_PATH}/fish_1_60.mp4`),
        resolveDatasetPath(`${FISH_DATASET_PATH}/fish_2_60.mp4`),
        resolveDatasetPath(`${FISH_DATASET_PATH}/fish_3_60.mp4`),
        resolveDatasetPath(`${FISH_DATASET_PATH}/fish_4_60.mp4`),
    ];
};
