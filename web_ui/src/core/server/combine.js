// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import { mergeFiles } from 'json-merger';

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);

const result = mergeFiles([
    path.resolve(dirname, './generated/account-service-spec.json'),
    path.resolve(dirname, './generated/gateway-api-spec.json'),
    path.resolve(dirname, './generated/credit-service-api-spec.json'),
    path.resolve(dirname, './generated/api-spec.json'),
]);
fs.writeFileSync(path.resolve(dirname, './generated/api-spec.json'), JSON.stringify(result, null, 2));
