// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Divider, Flex, Heading, Item, Picker, View } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import classes from './timm-model-configuration.module.scss';

const useGetTimmConfiguration = () => {
    return {
        architectures: [
            { id: '1', name: 'Architecture 1' },
            { id: '2', name: 'Architecture 2' },
        ],
        variants: [
            { id: '1', name: 'Variant 1' },
            { id: '2', name: 'Variant 2' },
        ],
        pretrainedWeights: [
            { id: '1', name: 'Pretrained Weights 1' },
            { id: '2', name: 'Pretrained Weights 2' },
        ],
        info: {
            parameters: '2 Millions',
            gigaFlops: '68.48',
            mAP: '31.2%',
            license: 'Apache-2.0',
        },
    };
};

export const TimmModelConfiguration = () => {
    const { t } = useTranslation();
    const { architectures, variants, pretrainedWeights, info } = useGetTimmConfiguration();

    return (
        <View UNSAFE_className={classes.container}>
            <Heading UNSAFE_className={classes.heading} level={3} marginBottom={'size-200'}>
                TIMM model configuration
            </Heading>

            <Flex>
                <Flex direction={'column'} gap={'size-200'} flex={2}>
                    <Flex gap={'size-300'}>
                        <Picker
                            width={'100%'}
                            items={architectures}
                            label={t('models.architectureFamilyLabel')}
                            placeholder={t('models.selectArchitecturePlaceholder')}
                        >
                            {(item) => <Item key={item.id}>{item.name}</Item>}
                        </Picker>
                        <Picker
                            width={'100%'}
                            items={variants}
                            label={t('models.modelVariantLabel')}
                            placeholder={t('models.selectVariantPlaceholder')}
                        >
                            {(item) => <Item key={item.id}>{item.name}</Item>}
                        </Picker>
                    </Flex>
                    <Picker
                        width={'100%'}
                        items={pretrainedWeights}
                        label={t('models.pretrainedWeightsLabel')}
                        placeholder={t('models.selectWeightsPlaceholder')}
                    >
                        {(item) => <Item key={item.id}>{item.name}</Item>}
                    </Picker>
                </Flex>

                <Divider size={'S'} marginX={'size-400'} orientation={'vertical'} />

                <ul className={classes.infoList}>
                    <li>{t('models.parametersLabel')}: {info.parameters}</li>
                    <li>GigaFlops: {info.gigaFlops}</li>
                    <li>mAP: {info.mAP}</li>
                    <li>License: {info.license}</li>
                </ul>
            </Flex>
        </View>
    );
};
