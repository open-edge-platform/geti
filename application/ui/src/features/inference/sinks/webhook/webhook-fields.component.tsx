// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Flex, Item, NumberField, Picker, TextField } from '@geti-ui/ui';

import { OutputFormats } from '../output-formats/output-formats.component';
import { RateLimitFields } from '../rate-limit/rate-limit-fields.component';
import { HeaderKeyValueBuilder } from './header-key-value-builder.component';
import { WebhookHttpMethod, type WebhookFormState } from './utils';

type WebhookFieldsProps = {
    value: WebhookFormState;
    onChange: (value: WebhookFormState) => void;
};

export const WebhookFields = ({ value, onChange }: WebhookFieldsProps) => {
    const { t } = useTranslation();

    return (
        <Flex direction='column' gap='size-200'>
            <TextField
                flex='1'
                label={t('common.labels.name')}
                value={value.name}
                onChange={(name) => onChange({ ...value, name })}
            />

            <Flex>
                <RateLimitFields
                    value={value.rate_limit ?? null}
                    onChange={(rate_limit) => onChange({ ...value, rate_limit })}
                />
            </Flex>

            <Flex direction={'row'} gap='size-200'>
                <Picker
                    flex='1'
                    label={t('inference.sinks.fields.httpMethod')}
                    selectedKey={value.http_method}
                    onSelectionChange={(key) => onChange({ ...value, http_method: key as WebhookHttpMethod })}
                >
                    <Item key={WebhookHttpMethod.POST}>{WebhookHttpMethod.POST}</Item>
                    <Item key={WebhookHttpMethod.PATCH}>{WebhookHttpMethod.PATCH}</Item>
                    <Item key={WebhookHttpMethod.PUT}>{WebhookHttpMethod.PUT}</Item>
                </Picker>
                <NumberField
                    label={t('inference.sinks.fields.timeout')}
                    minValue={1}
                    step={1}
                    value={value.timeout}
                    onChange={(timeout) => onChange({ ...value, timeout })}
                />
            </Flex>

            <TextField
                isRequired
                width={'100%'}
                label={t('inference.sinks.fields.webhookUrl')}
                value={value.webhook_url}
                onChange={(webhook_url) => onChange({ ...value, webhook_url })}
            />

            <OutputFormats
                value={value.output_formats}
                onChange={(output_formats) => onChange({ ...value, output_formats })}
            />

            <HeaderKeyValueBuilder value={value.headers} onChange={(headers) => onChange({ ...value, headers })} />
        </Flex>
    );
};
