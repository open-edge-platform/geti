// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { ANIMATION_PARAMETERS } from '@shared/animation-parameters/animation-parameters';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';
import { AnimatePresence, motion } from 'framer-motion';
import { useHover, useNumberFormatter } from 'react-aria';

import { Revisit } from '../../../../../assets/icons';

export interface AdjustmentHeaderProps {
    headerText: string;
    value: number;
    defaultValue: number;
    handleValueChange: (value: number) => void;
    formatOptions: Intl.NumberFormatOptions;
}

export const AdjustmentHeader = ({
    headerText,
    value,
    handleValueChange,
    formatOptions,
    defaultValue,
}: AdjustmentHeaderProps): JSX.Element => {
    const formatter = useNumberFormatter(formatOptions);
    const { hoverProps, isHovered } = useHover({});

    return (
        <div {...hoverProps}>
            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <Text>{headerText}</Text>
                <Flex alignItems={'center'} gap={'size-100'} height={'size-400'}>
                    <AnimatePresence>
                        {isHovered && (
                            <TooltipTrigger placement={'top'}>
                                <motion.div
                                    variants={ANIMATION_PARAMETERS.FADE_ITEM}
                                    initial={'hidden'}
                                    animate={'visible'}
                                    exit={'hidden'}
                                >
                                    <QuietActionButton
                                        onPress={() => handleValueChange(defaultValue)}
                                        aria-label={`Reset ${headerText.toLocaleLowerCase()}`}
                                    >
                                        <Revisit />
                                    </QuietActionButton>
                                </motion.div>
                                <Tooltip>{`Reset to default value ${headerText.toLocaleLowerCase()}`}</Tooltip>
                            </TooltipTrigger>
                        )}
                    </AnimatePresence>

                    <Text>{formatter.format(value)}</Text>
                </Flex>
            </Flex>
        </div>
    );
};
