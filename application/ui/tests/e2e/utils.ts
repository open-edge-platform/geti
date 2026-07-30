// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

export const getDirname = () => {
    const filename = fileURLToPath(import.meta.url);

    return path.dirname(filename);
};

export const getFilesToUpload = (relativePathToAssetDirectory: string) => {
    const dirname = getDirname();

    const files = fs.readdirSync(path.join(dirname, relativePathToAssetDirectory));
    console.log(files);
    return files.map((file) => path.join(dirname, './assets/lego-bricks-dataset', file));
};
