// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Tag } from '@geti/ui';

import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './model-card.module.scss';

export const ObsoleteTag: FC<{ id: string }> = ({ id }) => {
    return (
        <Tag
            withDot={false}
            text={`Obsolete`}
            id={`obsolete-algorithm-${idMatchingFormat(id)}-id`}
            data-testid={`obsolete-algorithm-${idMatchingFormat(id)}-id`}
            className={classes.obsoleteModelTag}
        />
    );
};
