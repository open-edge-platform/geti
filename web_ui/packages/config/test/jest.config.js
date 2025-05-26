// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fileURLToPath } from 'node:url';
import path from 'path';

const pathUrl = fileURLToPath(import.meta.url);
const dirname = path.dirname(pathUrl);

export default {
    setupFiles: ['react-app-polyfill/jsdom'],
    testEnvironment: 'jsdom',
    transform: {
        '^.+\\.(js|jsx|mjs|cjs|ts|tsx)$': path.resolve(dirname, './transformers/babelTransform.js'),
        '^.+\\.css$': path.resolve(dirname, './transformers/cssTransform.js'),
        '^(?!.*\\.(js|jsx|mjs|cjs|ts|tsx|css|json)$)': path.resolve(dirname, './transformers/fileTransform.js'),
    },
    transformIgnorePatterns: ['node_modules/?!(pretty-bytes)'],
    moduleNameMapper: {
        '^.+\\.module\\.(css|sass|scss)$': 'identity-obj-proxy',
    },
    moduleFileExtensions: ['web.js', 'js', 'web.ts', 'ts', 'web.tsx', 'tsx', 'json', 'web.jsx', 'jsx', 'node'],
    resetMocks: false,
    globalSetup: path.resolve(dirname, './jest.global.js'),
};
