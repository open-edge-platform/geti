// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { usePress } from 'react-aria';

import { ChevronUpLight } from '../../../../../assets/icons';
import { isVisualPromptModel } from '../../../../../core/annotations/services/visual-prompt-service';
import { PerformanceCategory } from '../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { ActionButton } from '../../../../../shared/components/button/button.component';
import { InfoTooltip } from '../../../../../shared/components/info-tooltip/info-tooltip.component';
import { Tag } from '../../../../../shared/components/tag/tag.component';
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
