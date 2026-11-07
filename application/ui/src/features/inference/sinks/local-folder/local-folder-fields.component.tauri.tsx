// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Flex, TextField } from '@geti-ui/ui';
import { open } from '@tauri-apps/plugin-dialog';

import { normalizeSelectedPath } from '../../shared/tauri-dialog';
import { OutputFormats } from '../output-formats/output-formats.component';
import { RateLimitFields } from '../rate-limit/rate-limit-fields.component';

type LocalFolderFieldsProps = {
    value: LocalFolderSinkConfig;
    onChange: (next: LocalFolderSinkConfig) => void;
};

export const LocalFolderFields = ({ value, onChange }: LocalFolderFieldsProps) => {
    const { t } = useTranslation();

    const handleOpenFolderDialog = () => {
        void open({
            directory: true,
            multiple: false,
            defaultPath: value.folder_path || undefined,
        })
            .then((selectedPath) => {
                const nextPath = normalizeSelectedPath(selectedPath);

                if (nextPath !== null) {
                    onChange({ ...value, folder_path: nextPath });
                }
            })
            .catch(console.error);
    };

    return (
        <Flex direction='column' gap='size-200'>
            <Flex gap='size-200'>
                <TextField
                    label={t('common.labels.name')}
                    value={value.name}
                    onChange={(name) => onChange({ ...value, name })}
                />
            </Flex>

            <Flex>
                <RateLimitFields
                    value={value.rate_limit ?? null}
                    onChange={(rate_limit) => onChange({ ...value, rate_limit })}
                />
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
                        label={t('inference.sinks.fields.folderPath')}
                        value={value.folder_path}
                    />
                </div>
            </Flex>

            <OutputFormats
                value={value.output_formats}
                onChange={(output_formats) => onChange({ ...value, output_formats })}
            />
        </Flex>
    );
};
