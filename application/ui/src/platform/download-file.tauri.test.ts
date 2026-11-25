// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { waitFor } from '@testing-library/react';

import { downloadFile } from './download-file.tauri';

const tauri = rs.hoisted(() => ({ invoke: rs.fn() }));

rs.mock('@tauri-apps/api/core', () => ({ invoke: tauri.invoke, Channel: class {} }));

describe('downloadFile (Tauri)', () => {
    afterEach(() => {
        rs.restoreAllMocks();
        tauri.invoke.mockReset();
    });

    it('hands the bytes of data URLs to the shell', async () => {
        // MSW would otherwise intercept fetching the data URL.
        rs.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(new Uint8Array([0, 1, 2, 255])));

        downloadFile('data:image/png;base64,AAEC/w==', 'chart.png');

        await waitFor(() =>
            expect(tauri.invoke).toHaveBeenCalledWith(
                'save_file',
                expect.objectContaining({ contents: [0, 1, 2, 255], fileName: 'chart.png' })
            )
        );
    });

    it('lets the shell download backend files', async () => {
        const url = 'https://localhost:7860/api/projects/p/models/m/variants/v/binary';

        downloadFile(url, 'model.zip');

        await waitFor(() =>
            expect(tauri.invoke).toHaveBeenCalledWith(
                'download_file',
                expect.objectContaining({ url, fileName: 'model.zip' })
            )
        );
    });
});
