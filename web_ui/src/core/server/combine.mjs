// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import { mergeFiles } from 'json-merger';

const __filename = fileURLToPath(import.meta.url);

const __dirname = path.dirname(__filename);

const result = mergeFiles([
    path.resolve(__dirname, './generated/account-service-spec.json'),
    path.resolve(__dirname, './generated/gateway-api-spec.json'),
    path.resolve(__dirname, './generated/credit-service-api-spec.json'),
    path.resolve(__dirname, './generated/api-spec.json'),
]);
fs.writeFileSync(path.resolve(__dirname, './generated/api-spec.json'), JSON.stringify(result, null, 2));
