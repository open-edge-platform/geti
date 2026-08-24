// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, ReactNode, useContext } from 'react';

import type { ModelArchitecture as ModelArchitectureType, ModelArchitectureWithPerformanceCategory } from '@/api/types';
import { Content, ContextualHelp, Divider, Flex, Heading, Radio, Text } from '@geti-ui/ui';
import { clsx } from 'clsx';
import { useTranslation } from 'react-i18next';

import { UltralyticsLicense } from '../../../components/ultralytics-license.component';
import { isUltralyticsModel } from '../../../utils';
import { getAccuracyMetric } from '../utils';

import classes from './model-architecture-card.module.scss';

const ModelArchitectureDescription = () => {
    const { modelArchitecture, isSelected } = useModelArchitecture();

    return (
        <ContextualHelp variant='info' UNSAFE_className={clsx({ [classes.description]: isSelected })}>
            <Heading>{modelArchitecture.name}</Heading>
            <Content>
                <Text>{modelArchitecture.description}</Text>
            </Content>
        </ContextualHelp>
    );
};

const ModelArchitectureDivider = () => {
    return <Divider size={'S'} />;
};

const License = () => {
    const { modelArchitecture } = useModelArchitecture();

    return (
        <li>
            {isUltralyticsModel(modelArchitecture.id) ? (
                <UltralyticsLicense />
            ) : (
                `License: ${modelArchitecture.license}`
            )}
        </li>
    );
};

const ModelArchitectureParameters = () => {
    const { t } = useTranslation();
    const { modelArchitecture } = useModelArchitecture();

    return (
        <ul className={classes.modelArchitectureParameters}>
            <li>{t("models.numberOfParams")}: {modelArchitecture.stats.trainable_parameters} million</li>
            <License />
        </ul>
    );
};

const ModelArchitectureDetailedParameters = () => {
    const { t } = useTranslation();
    const { modelArchitecture } = useModelArchitecture();
    const accuracyMetric = getAccuracyMetric(modelArchitecture);

    return (
        <ul className={classes.modelArchitectureParameters}>
            <li>{t("models.numberOfParams")}: {modelArchitecture.stats.trainable_parameters} million</li>
            <li>{t("models.gigaflops")}: {modelArchitecture.stats.gigaflops}</li>
            {accuracyMetric !== undefined && (
                <li>
                    {t(accuracyMetric.label)}: {accuracyMetric.value}%
                </li>
            )}
            <License />
        </ul>
    );
};

const ModelArchitectureName = () => {
    const { modelArchitecture, isSelected } = useModelArchitecture();

    return (
        <Flex justifyContent={'space-between'} alignItems={'center'} minWidth={0}>
            <Radio
                flex={1}
                minWidth={0}
                value={modelArchitecture.id}
                UNSAFE_className={clsx(classes.modelArchitectureName, {
                    [classes.modelArchitectureNameSelected]: isSelected,
                })}
            >
                {modelArchitecture.name}
            </Radio>
            <ModelArchitectureDescription />
        </Flex>
    );
};

type ModelArchitectureContextProps = {
    isSelected: boolean;
    modelArchitecture: ModelArchitectureType;
};

const ModelArchitectureContext = createContext<ModelArchitectureContextProps | null>(null);

const useModelArchitecture = () => {
    const context = useContext(ModelArchitectureContext);

    if (context === null) {
        throw new Error('useModelArchitecture was used outside of ModelArchitectureProvider');
    }

    return context;
};

type ModelArchitectureProps = {
    isSelected: boolean;
    children: ReactNode;
    onSelect: () => void;
    modelArchitecture: ModelArchitectureWithPerformanceCategory;
};

export const ModelArchitectureCard = ({
    isSelected,
    children,
    onSelect,
    modelArchitecture,
}: ModelArchitectureProps) => {
    const { t } = useTranslation();

    const getCategoryLabel = (category: string | undefined) => {
        if (category === undefined) return undefined;
        const keyMap: Record<string, string> = {
            speed: 'models.performanceSpeed',
            accuracy: 'models.performanceAccuracy',
            balance: 'models.performanceBalance',
        };
        return t(keyMap[category] ?? category, { defaultValue: category });
    };

    return (
        <ModelArchitectureContext value={{ isSelected, modelArchitecture }}>
            <div
                className={clsx(classes.modelArchitectureContainer, {
                    [classes.modelArchitectureSelected]: isSelected,
                })}
                onClick={onSelect}
                aria-label={
                    modelArchitecture.performanceCategory === undefined
                        ? modelArchitecture.name
                        : `${modelArchitecture.name} - ${getCategoryLabel(modelArchitecture.performanceCategory)}`
                }
                data-architecture-name={modelArchitecture.name}
            >
                {children}
            </div>
        </ModelArchitectureContext>
    );
};

ModelArchitectureCard.Name = ModelArchitectureName;
ModelArchitectureCard.Parameters = ModelArchitectureParameters;
ModelArchitectureCard.DetailedParameters = ModelArchitectureDetailedParameters;
ModelArchitectureCard.Divider = ModelArchitectureDivider;
ModelArchitectureCard.Description = ModelArchitectureDescription;
