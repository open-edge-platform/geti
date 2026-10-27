// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createContext, ReactNode, useContext, useMemo } from 'react';

import type { ModelArchitectureWithPerformanceCategory } from '@/api/types';
import { ThumbsUp } from '@/assets/icons';
import { useTranslation } from '@/i18n';
import { Content, ContextualHelp, Divider, Flex, Heading, Radio, Text } from '@geti-ui/ui';
import { clsx } from 'clsx';

import { ModelLicenseLink } from '../../../components/model-license-link.component';
import { ModelBadge } from '../../../model-listing/components/model-row/model-badge.component';
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
    const { t } = useTranslation();
    const { modelArchitecture } = useModelArchitecture();

    return (
        <li>
            {t('license.label')}
            <ModelLicenseLink license={modelArchitecture.license} />
        </li>
    );
};

const ModelArchitectureParameters = () => {
    const { modelArchitecture } = useModelArchitecture();
    const { t } = useTranslation();
    const accuracyMetric = getAccuracyMetric(modelArchitecture, t);

    return (
        <ul className={classes.modelArchitectureParameters}>
            {modelArchitecture.stats !== null && (
                <>
                    <li>
                        {t('models.training.architectures.card.numberOfParameters', {
                            count: modelArchitecture.stats.trainable_parameters,
                        })}
                    </li>
                    <li>
                        {t('models.training.architectures.card.gigaflops', {
                            value: modelArchitecture.stats.gigaflops,
                        })}
                    </li>
                </>
            )}
            {accuracyMetric !== undefined && (
                <li>
                    {accuracyMetric.label}: {accuracyMetric.value}%
                </li>
            )}
            <License />
        </ul>
    );
};

const ModelArchitectureRecommendedBadge = () => {
    const { t } = useTranslation();
    const { modelArchitecture } = useModelArchitecture();

    if (modelArchitecture.performanceCategory === undefined) {
        return null;
    }

    return (
        <ModelBadge color={'var(--spectrum-global-color-gray-100)'}>
            <ThumbsUp />
            <Text>{t('models.training.architectures.card.recommended')}</Text>
        </ModelBadge>
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
    modelArchitecture: ModelArchitectureWithPerformanceCategory;
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
    const value = useMemo(() => ({ isSelected, modelArchitecture }), [isSelected, modelArchitecture]);

    return (
        <ModelArchitectureContext value={value}>
            <div
                className={clsx(classes.modelArchitectureContainer, {
                    [classes.modelArchitectureSelected]: isSelected,
                })}
                onClick={onSelect}
                aria-label={modelArchitecture.name}
                data-architecture-name={modelArchitecture.name}
            >
                {children}
            </div>
        </ModelArchitectureContext>
    );
};

ModelArchitectureCard.Name = ModelArchitectureName;
ModelArchitectureCard.Parameters = ModelArchitectureParameters;
ModelArchitectureCard.RecommendedBadge = ModelArchitectureRecommendedBadge;
ModelArchitectureCard.Divider = ModelArchitectureDivider;
ModelArchitectureCard.Description = ModelArchitectureDescription;
