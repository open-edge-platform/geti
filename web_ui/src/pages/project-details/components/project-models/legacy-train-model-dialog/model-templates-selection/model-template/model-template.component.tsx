// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Heading, Radio, RadioGroup, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { PerformanceCategory } from '../../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { InfoTooltip } from '../../../../../../../shared/components/info-tooltip/info-tooltip.component';
import { ModelArchitectureTooltipText } from '../../../model-architecture-tooltip.component';
import { ActiveModelTag } from '../../../models-container/model-card/active-model-tag.component';
import { DeprecatedTag } from '../../../models-container/model-card/deprecated-model-tag.component';
import { RecommendedModelTag } from '../../../models-container/model-card/recommended-model-tag.component';
import { SelectableCard } from '../../../train-model-dialog/selectable-card/selectable-card.component';
import { isDeprecatedAlgorithm } from '../utils';

import classes from './model-template.module.scss';

interface ModelTemplateProps {
    template: SupportedAlgorithm;
    selectedModelTemplateId: string;
    handleSelectedTemplateId: (modelTemplateId: string | null) => void;
    activeModelTemplateIdPerTask: string | undefined;
}

export const ModelTemplate = ({
    template,
    selectedModelTemplateId,
    activeModelTemplateIdPerTask,
    handleSelectedTemplateId,
}: ModelTemplateProps): JSX.Element => {
    const { name, modelSize, modelTemplateId, performanceCategory, gigaflops, summary, license } = template;
    const isSelected = selectedModelTemplateId === modelTemplateId;
    const shouldShowActiveTag = modelTemplateId === activeModelTemplateIdPerTask;
    const isDeprecated = isDeprecatedAlgorithm(template.lifecycleStage);
    const showPerformanceCategory = performanceCategory && performanceCategory !== PerformanceCategory.OTHER;

    const handleOnPress = () => {
        handleSelectedTemplateId(modelTemplateId);
    };

    return (
        <SelectableCard
            headerContent={
                <>
                    <Flex justifyContent={'space-between'} alignItems={'center'} marginBottom={'size-50'}>
                        <RadioGroup
                            isEmphasized
                            aria-label={`Select ${name}`}
                            onChange={handleOnPress}
                            value={selectedModelTemplateId}
                            UNSAFE_className={classes.radioSelection}
                        >
                            <TooltipTrigger placement={'bottom'}>
                                <Radio
                                    value={modelTemplateId}
                                    aria-label={name}
                                    UNSAFE_className={classes.radioTrainTemplateName}
                                >
                                    <Heading
                                        UNSAFE_className={[
                                            classes.trainTemplateName,
                                            isSelected ? classes.selected : '',
                                        ].join(' ')}
                                    >
                                        {name}
                                    </Heading>
                                </Radio>
                                <Tooltip>{name}</Tooltip>
                            </TooltipTrigger>
                        </RadioGroup>
                        <InfoTooltip
                            id={`${name.toLocaleLowerCase()}-summary-id`}
                            tooltipText={
                                <ModelArchitectureTooltipText description={summary} isDeprecated={isDeprecated} />
                            }
                            iconColor={isSelected ? 'var(--energy-blue)' : undefined}
                        />
                    </Flex>
                    <Flex alignItems={'center'} gap={'size-100'}>
                        {shouldShowActiveTag && <ActiveModelTag id={name} className={classes.activeModelTag} />}
                        {showPerformanceCategory && (
                            <RecommendedModelTag
                                id={`${name.toLocaleLowerCase()}-recommended-tag-id`}
                                performanceCategory={performanceCategory}
                            />
                        )}
                        {isDeprecated && <DeprecatedTag id={`${name.toLocaleLowerCase()}`} />}
                    </Flex>
                </>
            }
            descriptionContent={
                <Flex alignItems={'center'} gap={'size-200'}>
                    <Flex direction={'column'}>
                        <Text UNSAFE_className={classes.subTitle}>Size</Text>
                        <Text>{modelSize} MB</Text>
                    </Flex>
                    <Flex direction={'column'}>
                        <Text UNSAFE_className={classes.subTitle}>Complexity</Text>
                        <Text>{gigaflops} GFlops</Text>
                    </Flex>
                    <Flex direction={'column'}>
                        <Text UNSAFE_className={classes.subTitle}>License</Text>
                        <Text>{license}</Text>
                    </Flex>
                </Flex>
            }
            text={name}
            isSelected={isSelected}
            handleOnPress={handleOnPress}
        />
    );
};
