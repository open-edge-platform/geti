// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Divider, Flex, Grid, Heading, Item, Loading, Picker, View } from '@geti-ui/ui';

import { ModelLicenseLink } from '../../components/model-license-link.component';
import { getAccuracyMetric } from '../model-architectures-list/utils';
import { useTrainModelState } from '../train-model-provider.component';

import classes from './timm-model-configuration.module.scss';

export const TimmModelConfiguration = () => {
    const { t } = useTranslation();
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

    const accuracyMetric =
        timmModelArchitecture === undefined ? undefined : getAccuracyMetric(timmModelArchitecture, t);
    const accuracyLabel = accuracyMetric?.label ?? t('models.training.architectures.metrics.top1AccOnImageNet');

    return (
        <View UNSAFE_className={classes.container}>
            <Heading UNSAFE_className={classes.heading} level={3} marginBottom={'size-200'}>
                {t('models.training.architectures.timm.heading')}
            </Heading>

            <Grid columns={'1fr auto .6fr'}>
                <Flex direction={'column'} gap={'size-200'} flex={2}>
                    <Flex gap={'size-300'}>
                        <Picker
                            width={'100%'}
                            label={t('models.training.architectures.timm.architectureFamilyLabel')}
                            placeholder={t('models.training.architectures.timm.selectArchitecturePlaceholder')}
                            selectedKey={selectedTimmFamily}
                            onSelectionChange={(key) => key !== null && onSelectTimmFamily(String(key))}
                        >
                            {timmFamilies.map((family) => (
                                <Item key={family}>{family}</Item>
                            ))}
                        </Picker>
                        <Picker
                            width={'100%'}
                            label={t('models.training.architectures.timm.modelVariantLabel')}
                            placeholder={t('models.training.architectures.timm.selectVariantPlaceholder')}
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
                        label={t('models.training.architectures.timm.pretrainedWeightsLabel')}
                        placeholder={t('models.training.architectures.timm.selectWeightsPlaceholder')}
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
                        <li>
                            {t('models.training.architectures.timm.parameters', {
                                count: timmModelArchitecture?.stats?.trainable_parameters ?? '-',
                            })}
                        </li>
                        <li>
                            {t('models.training.architectures.timm.gigaflops', {
                                value: timmModelArchitecture?.stats?.gigaflops ?? '-',
                            })}
                        </li>
                        <li>
                            {accuracyLabel}: {accuracyMetric?.value ?? '-'}%
                        </li>
                        <li>
                            {t('license.label')}
                            <ModelLicenseLink license={timmModelArchitecture?.license || { url: '', name: '' }} />
                        </li>
                    </ul>
                )}
            </Grid>
        </View>
    );
};
