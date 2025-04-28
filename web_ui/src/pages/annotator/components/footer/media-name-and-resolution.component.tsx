// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { PressableElement } from '../../../../shared/components/action-element/action-element.component';
import { trimText } from '../../../../shared/utils';

import classes from './annotator-footer.module.scss';

interface MediaNameAndResolutionProps {
    name: string;
    width: number;
    height: number;
    isLargeSize: boolean;
}

const LONG_TEXT_LENGTH = 200;
const SHORT_TEXT_LENGTH = 14;

export const MediaNameAndResolution = ({
    isLargeSize,
    name,
    width,
    height,
}: MediaNameAndResolutionProps): JSX.Element => {
    const paddingX = isLargeSize ? 'size-200' : 'size-100';
    const mediaName = trimText(name, isLargeSize ? LONG_TEXT_LENGTH : SHORT_TEXT_LENGTH);

    return (
        <View UNSAFE_className={`${classes.text} ${classes.metaItem}`} paddingX={paddingX}>
            <TooltipTrigger>
                <PressableElement aria-label='media name' UNSAFE_className={`${classes.text} ${classes.mediaName}`}>
                    <Text>{`${mediaName} (${width} px x ${height} px)`}</Text>
                </PressableElement>
                <Tooltip>{`${name} (${width} px x ${height} px)`}</Tooltip>
            </TooltipTrigger>
        </View>
    );
};
