// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { View } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';

import { TruncatedTextWithTooltip } from '../../../../shared/components/truncated-text/truncated-text.component';
import { isLargeSizeQuery } from '../../../../theme/queries';

import classes from './annotator-footer.module.scss';

const LONG_TEXT_LENGTH = 140;
const SHORT_TEXT_LENGTH = 60;

export const ProjectName = ({ name }: { name: string }): JSX.Element => {
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const paddingX = isLargeSize ? 'size-200' : 'size-100';

    return (
        <View UNSAFE_className={classes.metaItem} paddingX={paddingX} aria-label='project name'>
            <TruncatedTextWithTooltip
                UNSAFE_className={classes.text}
                width={isLargeSize ? LONG_TEXT_LENGTH : SHORT_TEXT_LENGTH}
            >
                {name}
            </TruncatedTextWithTooltip>
        </View>
    );
};
