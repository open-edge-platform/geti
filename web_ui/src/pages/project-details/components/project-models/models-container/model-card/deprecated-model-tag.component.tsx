// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Tag } from '@shared/components/tag/tag.component';

import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './model-card.module.scss';

export const DeprecatedTag: FC<{ id: string }> = ({ id }) => {
    return (
        <Tag
            withDot={false}
            text={`Deprecated`}
            id={`deprecated-algorithm-${idMatchingFormat(id)}-id`}
            data-testid={`deprecated-algorithm-${idMatchingFormat(id)}-id`}
            className={classes.deprecatedModelTag}
        />
    );
};
