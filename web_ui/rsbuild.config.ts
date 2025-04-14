// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
