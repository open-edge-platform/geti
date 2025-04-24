// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defineConfig, loadEnv } from '@rsbuild/core';
import { pluginNodePolyfill } from '@rsbuild/plugin-node-polyfill';
import { pluginReact } from '@rsbuild/plugin-react';
import { pluginSass } from '@rsbuild/plugin-sass';
import { pluginSvgr } from '@rsbuild/plugin-svgr';
import { RsdoctorRspackPlugin } from '@rsdoctor/rspack-plugin';

import { devProxy } from './dev-proxy';

const { publicVars, rawPublicVars } = loadEnv({ prefixes: ['REACT_APP_'] });

const publicPath = rawPublicVars['REACT_APP_PUBLIC_PATH'];

export default defineConfig({
    tools: {
        rspack: {
            plugins: [
                process.env.RSDOCTOR && new RsdoctorRspackPlugin({ supports: { generateTileGraph: true } }),
            ].filter(Boolean),
        },
    },
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
    environments: {
        dev: {
            source: {
                entry: {
                    index: './src/geti-dev-app.component.tsx',
                },
            },
            output: {
                distPath: {
                    root: 'build',
                },
                assetPrefix: publicPath,
            },
        },
        geti: {
            output: {
                distPath: {
                    root: 'build/app',
                },
                assetPrefix: publicPath,
            },
            source: {
                entry: {
                    index: './src/index.tsx',
                },
            },
        },
        admin: {
            output: {
                distPath: {
                    root: 'build/admin',
                },
                assetPrefix: '/intel-admin',
            },
            source: {
                entry: {
                    index: './src/intel-admin-app/index.component.tsx',
                },
            },
        },
    },
    html: {
        template: './public/index.html',
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
