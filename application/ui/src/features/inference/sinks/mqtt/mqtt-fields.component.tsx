// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MqttSinkConfig } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Flex, NumberField, Switch, TextField } from '@geti-ui/ui';

import { OutputFormats } from '../output-formats/output-formats.component';
import { RateLimitFields } from '../rate-limit/rate-limit-fields.component';

type MqttFieldsProps = {
    value: MqttSinkConfig;
    onChange: (value: MqttSinkConfig) => void;
};

export const MqttFields = ({ value, onChange }: MqttFieldsProps) => {
    const { t } = useTranslation();

    return (
        <Flex direction='column' gap='size-200'>
            <TextField
                width='100%'
                label={t('common.labels.name')}
                value={value.name}
                onChange={(name) => onChange({ ...value, name })}
            />
            <TextField
                isRequired
                width='100%'
                label={t('inference.sinks.fields.brokerHost')}
                value={value.broker_host}
                onChange={(broker_host) => onChange({ ...value, broker_host })}
            />
            <Flex gap='size-200'>
                <TextField
                    flex='1'
                    label={t('inference.sinks.fields.topic')}
                    value={value.topic}
                    onChange={(topic) => onChange({ ...value, topic })}
                />
                <NumberField
                    label={t('inference.sinks.fields.brokerPort')}
                    minValue={0}
                    step={1}
                    value={value.broker_port}
                    onChange={(port) => onChange({ ...value, broker_port: Number.isNaN(port) ? 0 : port })}
                />
            </Flex>
            <Flex gap='size-200' justifyContent='space-between' alignItems={'center'}>
                <RateLimitFields
                    value={value.rate_limit ?? null}
                    onChange={(rate_limit) => onChange({ ...value, rate_limit })}
                />
            </Flex>

            <Flex>
                <Switch
                    alignSelf='end'
                    aria-label='Require Authentication'
                    isSelected={value.auth_required}
                    onChange={(auth_required) => onChange({ ...value, auth_required })}
                >
                    {t('inference.sinks.fields.authRequired')}
                </Switch>
            </Flex>

            <OutputFormats
                value={value.output_formats}
                onChange={(output_formats) => onChange({ ...value, output_formats })}
            />
        </Flex>
    );
};
