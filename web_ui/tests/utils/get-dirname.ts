// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import path from 'path';
import { fileURLToPath } from 'url';

export const getDirname = (metaUrl: string) => {
    const filename = fileURLToPath(metaUrl);

    return path.dirname(filename);
};
