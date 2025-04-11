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

import { View } from '@adobe/react-spectrum';

import { TruncatedTextWithTooltip } from '../../../../shared/components/truncated-text/truncated-text.component';

import classes from './annotator-footer.module.scss';

interface MediaNameAndResolutionProps {
    isLargeSize: boolean;
    lastAnnotatorId: string;
}

export const LastAnnotator = ({ lastAnnotatorId, isLargeSize }: MediaNameAndResolutionProps): JSX.Element => {
    const paddingX = isLargeSize ? 'size-200' : 'size-100';

    return (
        <View UNSAFE_className={`${classes.text} ${classes.metaItem}`} paddingX={paddingX}>
            <TruncatedTextWithTooltip
                maxWidth={'size-3000'}
                aria-label={'last annotator'}
                UNSAFE_className={`${classes.text} ${classes.mediaName}`}
            >{`Last annotator: ${lastAnnotatorId}`}</TruncatedTextWithTooltip>
        </View>
    );
};
