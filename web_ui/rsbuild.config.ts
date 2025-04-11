// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { defineConfig, loadEnv } from '@rsbuild/core';
import { pluginNodePolyfill } from '@rsbuild/plugin-node-polyfill';
import { pluginReact } from '@rsbuild/plugin-react';
import { pluginSass } from '@rsbuild/plugin-sass';
import { pluginSvgr } from '@rsbuild/plugin-svgr';

import { devProxy } from './dev-proxy';

const { publicVars, rawPublicVars } = loadEnv({ prefixes: ['REACT_APP_'] });

const publicPath = rawPublicVars['REACT_APP_PUBLIC_PATH'];

export default defineConfig({
    plugins: [
        // Needed for React, JSX, etc
        pluginReact(),
        // Needed for sass support
        pluginSass(),
        // Needed for svg support
        pluginSvgr({
            svgrOptions: {
                exportType: 'named',
            },
        }),
        // Needed for node functions like 'path'
        pluginNodePolyfill(),
    ],
    html: {
        template: './public/index.html',
    },
    output: {
        distPath: {
            root: 'build',
        },
        assetPrefix: publicPath,
    },
    source: {
        define: {
            ...publicVars,
            // Copy all REACT_APP_* to process.env
            'process.env': JSON.stringify(rawPublicVars),
        },
    },
    server: {
        proxy: devProxy,
    },
});
