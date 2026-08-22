// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from 'react';

import type { LocalFolderSinkConfig } from '@/api/types';
import { Flex, TextField } from '@geti-ui/ui';
import { open } from '@tauri-apps/plugin-dialog';
import { useTranslation } from 'react-i18next';

import { normalizeSelectedPath } from '../../shared/tauri-dialog';
import { OutputFormats } from '../output-formats/output-formats.component';
import { RateLimitFields } from '../rate-limit/rate-limit-fields.component';

type LocalFolderProps = {
    defaultState: LocalFolderSinkConfig;
};

export const LocalFolder = ({ defaultState }: LocalFolderProps) => {
    const { t } = useTranslation();

    const [folderPath, setFolderPath] = useState(defaultState.folder_path);

    useEffect(() => {
        setFolderPath(defaultState.folder_path);
    }, [defaultState.folder_path]);

    const handleOpenFolderDialog = useCallback(() => {
        void open({
            directory: true,
            multiple: false,
            defaultPath: folderPath || undefined,
        })
            .then((selectedPath) => {
                const nextPath = normalizeSelectedPath(selectedPath);

                if (nextPath !== null) {
                    setFolderPath(nextPath);
                }
            })
            .catch(console.error);
    }, [folderPath]);

    return (
        <Flex direction='column' gap='size-200'>
            <TextField isHidden label='id' name='id' defaultValue={defaultState.id} />

            <Flex gap='size-200'>
                <TextField
                    label={t('inference.nameLabel')}
                    name='name'
                    defaultValue={defaultState.name || t('inference.localFolderSinkDefaultName')}
                />
            </Flex>

            <Flex>
                <RateLimitFields rateLimit={defaultState.rate_limit} />
            </Flex>

            <Flex gap='size-50'>
                <div
                    onClick={handleOpenFolderDialog}
                    onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleOpenFolderDialog()}
                    role='button'
                    tabIndex={0}
                    style={{ width: '100%', cursor: 'pointer' }}
                >
                    <TextField
                        isRequired
                        isReadOnly
                        width={'100%'}
                        label={t('inference.folderPathLabel')}
                        name='folder_path'
                        value={folderPath}
                    />
                </div>
            </Flex>

            <OutputFormats config={defaultState.output_formats} />
        </Flex>
    );
};
