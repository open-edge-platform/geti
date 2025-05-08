// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as path from 'path';

import { getDirname } from './get-dirname';

export const resolveTestAssetPath = (...p: string[]) => {
    return path.resolve(getDirname(import.meta.url), './../../src/assets/tests-assets/', ...p);
};

export const resolveAntelopePath = () => {
    return resolveTestAssetPath('antelope.png');
};

export const resolveDatasetPath = (...p: string[]) => {
    return path.resolve(getDirname(import.meta.url), './../datasets', ...p);
};

export const resolveMockFilesPath = (...p: string[]) => {
    return path.resolve(getDirname(import.meta.url), './../mockFiles', ...p);
};
