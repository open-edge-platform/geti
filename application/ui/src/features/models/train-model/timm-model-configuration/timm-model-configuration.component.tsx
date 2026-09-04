// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Divider, Flex, Grid, Heading, Item, Loading, Picker, View } from '@geti-ui/ui';

import { getAccuracyMetric } from '../model-architectures-list/utils';
import { useTrainModelState } from '../train-model-provider.component';

import classes from './timm-model-configuration.module.scss';

export const TimmModelConfiguration = () => {
    const {
        timmFamilies,
        timmVariants,
        timmPretrainedTags,
        selectedTimmFamily,
        onSelectTimmFamily,
        selectedTimmVariant,
        onSelectTimmVariant,
        selectedTimmPretrainedTag,
        onSelectTimmPretrainedTag,
        timmModelArchitecture,
        isLoadingTimmModelArchitecture,
    } = useTrainModelState();

    const accuracyMetric = timmModelArchitecture === undefined ? undefined : getAccuracyMetric(timmModelArchitecture);

    return (
        <View UNSAFE_className={classes.container}>
            <Heading UNSAFE_className={classes.heading} level={3} marginBottom={'size-200'}>
                TIMM model configuration
            </Heading>

            <Grid columns={'1fr auto .6fr'}>
                <Flex direction={'column'} gap={'size-200'} flex={2}>
                    <Flex gap={'size-300'}>
                        <Picker
                            width={'100%'}
                            label={'Architecture family'}
                            placeholder={'Select architecture'}
                            selectedKey={selectedTimmFamily}
                            onSelectionChange={(key) => key !== null && onSelectTimmFamily(String(key))}
                        >
                            {timmFamilies.map((family) => (
                                <Item key={family}>{family}</Item>
                            ))}
                        </Picker>
                        <Picker
                            width={'100%'}
                            label={'Model variant'}
                            placeholder={'Select variant'}
                            isDisabled={selectedTimmFamily === null}
                            selectedKey={selectedTimmVariant}
                            onSelectionChange={(key) => key !== null && onSelectTimmVariant(String(key))}
                        >
                            {timmVariants.map((variant) => (
                                <Item key={variant}>{variant}</Item>
                            ))}
                        </Picker>
                    </Flex>
                    <Picker
                        width={'100%'}
                        label={'Pretrained Weights'}
                        placeholder={'Select weights'}
                        isDisabled={selectedTimmVariant === null}
                        selectedKey={selectedTimmPretrainedTag}
                        onSelectionChange={(key) => key !== null && onSelectTimmPretrainedTag(String(key))}
                    >
                        {timmPretrainedTags.map((pretrainedTag) => (
                            <Item key={pretrainedTag}>{pretrainedTag}</Item>
                        ))}
                    </Picker>
                </Flex>

                <Divider size={'S'} marginX={'size-400'} orientation={'vertical'} />

                {isLoadingTimmModelArchitecture ? (
                    <Loading mode={'inline'} size={'M'} aria-label={'Loading model statistics'} />
                ) : (
                    <ul className={classes.infoList}>
                        <li>Parameters: {timmModelArchitecture?.stats?.trainable_parameters ?? '-'} million</li>
                        <li>GigaFlops: {timmModelArchitecture?.stats?.gigaflops ?? '-'}</li>
                        <li>
                            {accuracyMetric?.label ?? 'Top-1 Acc on ImageNet'}: {accuracyMetric?.value ?? '-'}%
                        </li>
                        <li>License: {timmModelArchitecture?.license ?? '-'}</li>
                    </ul>
                )}
            </Grid>
        </View>
    );
};
