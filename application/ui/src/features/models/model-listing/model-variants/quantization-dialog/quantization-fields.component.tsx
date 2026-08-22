// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode, useState } from 'react';

import {
    ActionButton,
    Checkbox,
    Content,
    ContextualHelp,
    Flex,
    Grid,
    NumberField,
    Slider,
    Text,
    View,
} from '@geti-ui/ui';
import { Refresh } from '@geti-ui/ui/icons';
import { useTranslation } from 'react-i18next';

export const DEFAULT_QUANTIZATION_PARAMETERS = {
    accuracyDrop: 1.0,
    calibrationSize: 200,
    maxNumIterations: 10,
    hasNoMaxAccuracyDrop: true,
    usesFullCalibrationDataset: false,
};

type QuantizationFieldLayoutProps = {
    children: ReactNode;
    onReset: () => void;
};
const QuantizationFieldLayout = ({ children, onReset }: QuantizationFieldLayoutProps) => {
    const { t } = useTranslation();

    return (
        <Grid columns={['1fr', '.1fr', 'size-3400', '1fr', '.2fr']} alignItems={'center'} gap={'size-200'}>
            {children}

            <ActionButton isQuiet aria-label={t('models.resetToDefault')} onPress={onReset}>
                <Refresh />
            </ActionButton>
        </Grid>
    );
};

type MaxAccuracyDropFieldProps = {
    value: number;
    onChange: (value: number) => void;
    isDisabled: boolean;
    onDisabledChange: (isDisabled: boolean) => void;
    onReset: () => void;
};

export const MaxAccuracyDropField = ({
    value,
    onChange,
    isDisabled,
    onDisabledChange,
    onReset,
}: MaxAccuracyDropFieldProps) => {
    const { t } = useTranslation();
    const [draftValue, setDraftValue] = useState<number | null>(null);
    const parameterValue = draftValue ?? value;

    const handleValueChange = (inputValue: number) => {
        setDraftValue(null);
        onChange(inputValue);
    };

    return (
        <QuantizationFieldLayout onReset={onReset}>
            <Text>{t('models.maxAccuracyDrop')}</Text>
            <ContextualHelp>
                <Content>
                    Maximum allowed drop in validation accuracy.
                    <br />
                    <br />
                    Beware that accuracy-aware quantization may take a long time when the max allowed drop is small.
                    <br />
                    <br />
                    Also note that the final testing accuracy may be lower than the specified validation accuracy
                    threshold, especially for relatively small datasets.
                </Content>
            </ContextualHelp>
            <Flex gap={'size-100'}>
                <Slider
                    aria-label={t('models.changeMaxAccuracyDropSlider')}
                    value={parameterValue}
                    minValue={0.1}
                    maxValue={15}
                    step={0.1}
                    onChange={setDraftValue}
                    onChangeEnd={handleValueChange}
                    isFilled
                    flex={1}
                    isDisabled={isDisabled}
                />
                <NumberField
                    hideStepper
                    step={0.1}
                    value={parameterValue}
                    minValue={0.1}
                    maxValue={15}
                    onChange={handleValueChange}
                    isDisabled={isDisabled}
                    aria-label={t('models.changeMaxAccuracyDrop')}
                    formatOptions={{ maximumFractionDigits: 1 }}
                />
            </Flex>
            <Checkbox aria-label={t('models.noMaximumCheckbox')} isSelected={isDisabled} onChange={onDisabledChange}>
                No maximum
            </Checkbox>
        </QuantizationFieldLayout>
    );
};

type MaxNumIterationsFieldProps = {
    value: number;
    onChange: (value: number) => void;
    isDisabled: boolean;
    onReset: () => void;
};

export const MaxNumIterationsField = ({ value, onChange, isDisabled, onReset }: MaxNumIterationsFieldProps) => {
    const { t } = useTranslation();
    return (
        <QuantizationFieldLayout onReset={onReset}>
            <Text>{t('models.maxIterations')}</Text>
            <ContextualHelp>
                <Content>
                    Maximum number of iterations of accuracy-aware quantization.
                    <br />
                    <br />
                    Accuracy-aware quantization iteratively removes model layers from the quantization scope until the
                    max accuracy drop criteria is met. Limiting the number of iterations can significantly reduce the
                    time it takes to quantize models with many layers.
                    <br />
                    <br />
                    This parameter is only used when a max accuracy drop is set.
                </Content>
            </ContextualHelp>
            <Flex gap={'size-100'}>
                <NumberField
                    hideStepper
                    step={1}
                    value={value}
                    minValue={1}
                    onChange={onChange}
                    isDisabled={isDisabled}
                    aria-label={t('models.changeMaxIterations')}
                    formatOptions={{ maximumFractionDigits: 0 }}
                    flex={1}
                />
            </Flex>
            <View />
        </QuantizationFieldLayout>
    );
};

type CalibrationDatasetSizeFieldProps = {
    value: number;
    onChange: (value: number) => void;
    maxValue: number;
    isDisabled: boolean;
    onDisabledChange: (isDisabled: boolean) => void;
    onReset: () => void;
};

export const CalibrationDatasetSizeField = ({
    value,
    onChange,
    maxValue,
    isDisabled,
    onDisabledChange,
    onReset,
}: CalibrationDatasetSizeFieldProps) => {
    const { t } = useTranslation();
    const [draftValue, setDraftValue] = useState<number | null>(null);
    const parameterValue = draftValue ?? value;

    const handleValueChange = (inputValue: number) => {
        setDraftValue(null);
        onChange(inputValue);
    };

    return (
        <QuantizationFieldLayout onReset={onReset}>
            <Text>{t('models.maxCalibrationSize')}</Text>

            <ContextualHelp>
                <Content>{t('models.calibrationNote')}</Content>
            </ContextualHelp>

            <Flex gap={'size-100'}>
                <Slider
                    aria-label={t('models.changeCalibrationSizeSlider')}
                    value={parameterValue}
                    minValue={1}
                    maxValue={maxValue}
                    step={1}
                    onChange={setDraftValue}
                    onChangeEnd={handleValueChange}
                    isFilled
                    flex={1}
                    isDisabled={isDisabled}
                />
                <NumberField
                    hideStepper
                    step={1}
                    value={parameterValue}
                    minValue={1}
                    maxValue={maxValue}
                    onChange={handleValueChange}
                    isDisabled={isDisabled}
                    aria-label={t('models.changeCalibrationSize')}
                />
            </Flex>
            <Checkbox
                aria-label={t('models.useFullDatasetCheckbox')}
                isSelected={isDisabled}
                onChange={onDisabledChange}
            >
                Use full dataset
            </Checkbox>
        </QuantizationFieldLayout>
    );
};
