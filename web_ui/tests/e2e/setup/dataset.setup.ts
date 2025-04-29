// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import fs from 'fs';
import http from 'http';

import AdmZip from 'adm-zip';

import { resolveDatasetPath } from '../../utils/dataset';
import { setup } from './fixture';

setup('Download and extract datasets for e2e tests', async ({}) => {
    await setup.step('Download and extract datasets', async () => {
        const outputPath = resolveDatasetPath('');
        const url = process.env.E2E_DATASET_URL;

        if (fs.existsSync(resolveDatasetPath('cards'))) {
            console.info('Playwright datasets already exists, skipping download and extraction step', outputPath);
            return;
        }

        if (url === '' || url === undefined) {
            throw new Error('Unable to download datasets required for E2E tests, please configure the E2E_DATASET_URL');
        }

        const datasetZip = resolveDatasetPath('../pw_datasets.zip');

        console.info(`Downloading datasets from ${url}`);
        await new Promise<void>((resolve, reject) => {
            http.get(url, function (response) {
                if (response.statusCode !== 200) {
                    console.error('Could not find file');
                    return;
                }

                response.pipe(fs.createWriteStream(datasetZip)).on('close', resolve).on('error', reject);
            }).on('error', (error) => {
                console.error('Error during download', error);
                reject(error);
            });
        });

        console.info('Downloaded datasets done');
        console.info(`Extracting datasets to ${outputPath}`);
        const zip = new AdmZip(datasetZip);
        zip.extractAllTo(outputPath);
        console.info('Extracting datasets done');
    });
});
