// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@geti/ui';

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
