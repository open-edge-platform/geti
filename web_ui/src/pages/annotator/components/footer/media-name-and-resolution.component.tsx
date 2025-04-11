// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { ActionElement } from '../../../../shared/components/action-element/action-element.component';
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
                <ActionElement aria-label='media name' UNSAFE_className={`${classes.text} ${classes.mediaName}`}>
                    {`${mediaName} (${width} px x ${height} px)`}
                </ActionElement>
                <Tooltip>{`${name} (${width} px x ${height} px)`}</Tooltip>
            </TooltipTrigger>
        </View>
    );
};
