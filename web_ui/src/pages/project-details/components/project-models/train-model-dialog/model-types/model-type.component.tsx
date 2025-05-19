// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { Flex, Grid, Heading, Radio, RadioGroup, repeat, Tooltip, TooltipTrigger } from '@geti/ui';
import clsx from 'clsx';
import { isFunction } from 'lodash-es';

import { SupportedAlgorithm } from '../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { InfoTooltip } from '../../../../../../shared/components/info-tooltip/info-tooltip.component';
import { isDeprecatedAlgorithm } from '../../legacy-train-model-dialog/model-templates-selection/utils';
import { ModelArchitectureTooltipText } from '../../model-architecture-tooltip.component';
import { ActiveModelTag } from '../../models-container/model-card/active-model-tag.component';
import { DeprecatedTag } from '../../models-container/model-card/deprecated-model-tag.component';
import { SelectableCard } from '../selectable-card/selectable-card.component';
import { AttributeRating, Ratings } from './attribute-rating/attribute-rating.component';

import classes from './model-type.module.scss';

interface ModelTypeProps {
    name: string;
    algorithm: SupportedAlgorithm;
    selectedModelTemplateId: string | null;
    onChangeSelectedTemplateId: (modelTemplateId: string | null) => void;
    activeModelTemplateId: string | null;
    renderTag: (() => ReactNode) | undefined;
}

interface TemplateRatingProps {
    ratings: {
        inferenceSpeed: Ratings;
        trainingTime: Ratings;
        accuracy: Ratings;
    };
}

const TemplateRating: FC<TemplateRatingProps> = ({ ratings }) => {
    return (
        <Grid columns={repeat(3, '1fr')} justifyContent={'space-evenly'} gap={'size-250'}>
            <AttributeRating name={'Inference speed'} rating={ratings.inferenceSpeed} />
            <AttributeRating name={'Training time'} rating={ratings.trainingTime} />
            <AttributeRating name={'Accuracy'} rating={ratings.accuracy} />
        </Grid>
    );
};

export const ModelType: FC<ModelTypeProps> = ({
    algorithm,
    selectedModelTemplateId,
    onChangeSelectedTemplateId,
    activeModelTemplateId,
    renderTag,
    name,
}) => {
    const { modelTemplateId, lifecycleStage, summary } = algorithm;
    const isSelected = selectedModelTemplateId === modelTemplateId;

    const shouldShowActiveTag = modelTemplateId === activeModelTemplateId;

    const isDeprecated = isDeprecatedAlgorithm(lifecycleStage);

    const handlePress = () => {
        onChangeSelectedTemplateId(modelTemplateId);
    };

    return (
        <SelectableCard
            isSelected={isSelected}
            handleOnPress={handlePress}
            text={name}
            headerContent={
                <>
                    <Flex alignItems={'center'} marginBottom={'size-50'}>
                        <RadioGroup
                            isEmphasized
                            aria-label={`Select ${name}`}
                            onChange={handlePress}
                            value={selectedModelTemplateId}
                        >
                            <TooltipTrigger placement={'bottom'}>
                                <Radio
                                    value={modelTemplateId}
                                    aria-label={name}
                                    UNSAFE_className={classes.radioTrainTemplateName}
                                >
                                    <Heading
                                        UNSAFE_className={clsx(classes.trainTemplateName, {
                                            [classes.selected]: isSelected,
                                        })}
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
                            className={classes.infoTooltip}
                        />
                    </Flex>
                    <Flex alignItems={'center'} gap={'size-100'}>
                        {shouldShowActiveTag && <ActiveModelTag id={name} />}
                        {isFunction(renderTag) && renderTag()}
                        {isDeprecated && <DeprecatedTag id={`${name.toLocaleLowerCase()}`} />}
                    </Flex>
                </>
            }
            descriptionContent={
                <TemplateRating ratings={{ accuracy: 'HIGH', trainingTime: 'MEDIUM', inferenceSpeed: 'LOW' }} />
            }
        />
    );
};
