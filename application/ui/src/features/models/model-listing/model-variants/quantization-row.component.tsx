// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Model } from '@/api/types';
import { Button, Content, ContextualHelp, DialogTrigger, Flex, Text } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { QuantizationDialog } from './quantization-dialog/quantization-dialog.component';

type QuantizationRowProps = {
    model: Model;
    isDisabled?: boolean;
};
export const QuantizationRow = ({ model, isDisabled = false }: QuantizationRowProps) => {
    const { t } = useTranslation();

    return (
        <Flex marginTop={'size-150'} alignItems={'center'} justifyContent={'space-between'}>
            <Flex>
                <Text>{t('models.optimizeNncfText')}</Text>
                <ContextualHelp>
                    <Content>
                        OpenVINO NNCF (Neural Network Compression Framework) via INT8 quantization reduces model size
                        and speeds up inference with minimal impact on accuracy
                    </Content>
                </ContextualHelp>
            </Flex>
            <DialogTrigger>
                <Button variant={'secondary'} isDisabled={isDisabled}>
                    Start quantization
                </Button>
                {(close) => <QuantizationDialog model={model} onClose={close} />}
            </DialogTrigger>
        </Flex>
    );
};
