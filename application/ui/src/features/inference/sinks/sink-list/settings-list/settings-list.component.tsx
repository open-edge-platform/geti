// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SinkConfig, SinkOutputFormats, WebhookSinkConfig } from '@/api/types';
import { useTranslation } from 'react-i18next';

import { removeUnderscore } from '../../../util';
import { formatRateLimit } from '../../utils';
import { getPairsFromObject } from '../../webhook/utils';

import classes from './settings-list.module.scss';

type SettingsListProps = {
    sink: SinkConfig;
};

const OutputFormats = ({ outputFormats }: { outputFormats: SinkOutputFormats }) => {
    return (
        <ul>
            {outputFormats.map((item) => (
                <li key={item}>{removeUnderscore(item)}</li>
            ))}
        </ul>
    );
};

const WebhookHeaders = ({ sink }: { sink: WebhookSinkConfig }) => {
    return (
        <ul>
            {getPairsFromObject(sink.headers ?? {}).map((pair) => (
                <li key={pair.key}>
                    {pair.key}: {pair.value}
                </li>
            ))}
        </ul>
    );
};

export const SettingsList = ({ sink }: SettingsListProps) => {
    const { t } = useTranslation();

    const rateLimitText = formatRateLimit(sink.rate_limit);
    const outputFormatsLine = (
        <li>
            {t('inference.outputFormatsLabel')}: <OutputFormats outputFormats={sink.output_formats} />
        </li>
    );

    if (sink.sink_type === 'folder') {
        return (
            <ul className={classes.list}>
                <li>
                    {t('inference.folderPathLabel')}: {sink.folder_path}
                </li>
                <li>
                    {t('inference.rateLimitLabel')}: {rateLimitText}
                </li>
                {outputFormatsLine}
            </ul>
        );
    }

    if (sink.sink_type === 'webhook') {
        return (
            <ul className={classes.list}>
                <li>
                    {t('inference.rateLimitLabel')}: {rateLimitText}
                </li>
                <li>
                    {t('inference.httpMethodDetail')}: {sink.http_method}
                </li>
                <li>
                    {t('inference.timeoutDetail')}: {sink.timeout}
                </li>
                <li>
                    {t('inference.webhookUrlLabelDetail')}: {sink.webhook_url}
                </li>
                <li>
                    {t('inference.headersLabel')} <WebhookHeaders sink={sink} />
                </li>
                {outputFormatsLine}
            </ul>
        );
    }

    if (sink.sink_type === 'mqtt') {
        return (
            <ul className={classes.list}>
                <li>
                    {t('inference.topicLabelDetail')}: {sink.topic}
                </li>
                <li>
                    {t('inference.rateLimitLabel')}: {rateLimitText}
                </li>
                <li>
                    {t('inference.authRequiredDetail')}: {sink.auth_required ? t('common.yes') : t('common.no')}
                </li>
                <li>
                    {t('inference.brokerHostDetail')}: {sink.broker_host}
                </li>
                <li>
                    {t('inference.brokerPortDetail')}: {sink.broker_port}
                </li>
                {outputFormatsLine}
            </ul>
        );
    }

    if (sink.sink_type === 'ros') {
        return (
            <ul className={classes.list}>
                <li>
                    {t('inference.topicLabelDetail')}: {sink.topic}
                </li>
                <li>
                    {t('inference.rateLimitLabel')}: {rateLimitText}
                </li>
                {outputFormatsLine}
            </ul>
        );
    }

    return <></>;
};
