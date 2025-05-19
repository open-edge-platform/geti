// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMediaQuery, View } from '@geti/ui';

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
