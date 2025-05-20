// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Flex, Heading, Tag } from '@geti/ui';
import { ChevronUpLight } from '@geti/ui/icons';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { usePress } from 'react-aria';

import { isVisualPromptModel } from '../../../../../core/annotations/services/visual-prompt-service';
import { PerformanceCategory } from '../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { InfoTooltip } from '../../../../../shared/components/info-tooltip/info-tooltip.component';
import { ModelArchitectureTooltipText } from '../model-architecture-tooltip.component';
import { DeprecatedTag } from './model-card/deprecated-model-tag.component';
import { ObsoleteTag } from './model-card/obsolete-model-tag.component';
import { RecommendedModelTag } from './model-card/recommended-model-tag.component';

import classes from './models-container.module.scss';

interface ModelsContainerHeaderProps {
    onClick: () => void;
    isObsolete: boolean;
    isDeprecated: boolean;
    hasManyModels: boolean;
    groupId: string;
    groupName: string;
    performanceCategory: PerformanceCategory;
    areModelsExpanded: boolean;
    modelSummary: string;
}

export const ModelsContainerHeader = ({
    onClick,
    groupName,
    groupId,
    areModelsExpanded,
    hasManyModels,
    performanceCategory,
    isObsolete,
    isDeprecated,
    modelSummary,
}: ModelsContainerHeaderProps): JSX.Element => {
    const { pressProps } = usePress({ onPress: onClick });

    const shouldShowPerformanceCategory = performanceCategory !== PerformanceCategory.OTHER;

    return (
        <div {...pressProps}>
            <Flex
                alignItems={'center'}
                justifyContent={'space-between'}
                UNSAFE_className={clsx(
                    classes.container,
                    isObsolete && classes.obsolete,
                    hasManyModels && classes.containerHovered
                )}
                id={`models-container-${groupId}`}
            >
                <Flex gap={'size-100'} alignItems={'center'}>
                    <Heading id={`model-group-name-${groupId}-id`} margin={0}>
                        {groupName}
                    </Heading>
                    {shouldShowPerformanceCategory && (
                        <RecommendedModelTag id={groupId} performanceCategory={performanceCategory} />
                    )}
                    {isObsolete && <ObsoleteTag id={groupId} />}
                    {isDeprecated && <DeprecatedTag id={groupId} />}
                    {isVisualPromptModel({ groupName }) ? (
                        <Tag text='Beta' />
                    ) : (
                        <InfoTooltip
                            id={`algorithm-summary-${groupId}-id`}
                            tooltipText={
                                <ModelArchitectureTooltipText
                                    description={modelSummary}
                                    isDeprecated={isDeprecated}
                                    isObsolete={isObsolete}
                                />
                            }
                        />
                    )}
                </Flex>
                <Flex gap={'size-150'} alignItems={'center'}>
                    {hasManyModels && (
                        <ActionButton
                            isQuiet
                            id={`expand-button-${groupId}-id`}
                            aria-label={'expand button'}
                            onPress={onClick}
                        >
                            <motion.div animate={{ rotate: areModelsExpanded ? 0 : 180 }}>
                                <ChevronUpLight
                                    id={'chevron-up-id'}
                                    aria-label={areModelsExpanded ? 'Hide models' : 'Expand models'}
                                />
                            </motion.div>
                        </ActionButton>
                    )}
                </Flex>
            </Flex>
        </div>
    );
};
