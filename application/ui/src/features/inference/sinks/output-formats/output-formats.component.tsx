// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SinkOutputFormats } from '@/api/types';
import { Checkbox, CheckboxGroup } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { OutputFormat } from '../utils';

import classes from './output-formats.module.scss';

type OutputFormatsProps = {
    config?: SinkOutputFormats;
};

export const OutputFormats = ({ config = [] }: OutputFormatsProps) => {
    const { t } = useTranslation();

    return (
        <CheckboxGroup
            isRequired
            label={t('inference.outputFormatsLabel')}
            name='output_formats'
            defaultValue={config}
            UNSAFE_className={classes.itemList}
        >
            <Checkbox name='output_formats' value={OutputFormat.PREDICTIONS}>
                Predictions
            </Checkbox>
            <Checkbox name='output_formats' value={OutputFormat.IMAGE_ORIGINAL}>
                Image Original
            </Checkbox>
            <Checkbox name='output_formats' value={OutputFormat.IMAGE_WITH_PREDICTIONS}>
                Image with Predictions
            </Checkbox>
        </CheckboxGroup>
    );
};
