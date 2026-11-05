// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Flex, TextField } from '@geti-ui/ui';

import { OutputFormats } from '../output-formats/output-formats.component';
import { RateLimitFields } from '../rate-limit/rate-limit-fields.component';

type LocalFolderFieldsProps = {
    value: LocalFolderSinkConfig;
    onChange: (next: LocalFolderSinkConfig) => void;
};

export const LocalFolderFields = ({ value, onChange }: LocalFolderFieldsProps) => {
    const { t } = useTranslation();

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
                <TextField
                    isRequired
                    width={'100%'}
                    label={t('inference.sinks.fields.folderPath')}
                    value={value.folder_path}
                    onChange={(folder_path) => onChange({ ...value, folder_path })}
                />
            </Flex>

            <OutputFormats
                value={value.output_formats}
                onChange={(output_formats) => onChange({ ...value, output_formats })}
            />
        </Flex>
    );
};
