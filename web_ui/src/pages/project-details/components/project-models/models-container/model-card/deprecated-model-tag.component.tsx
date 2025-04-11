// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Tag } from '../../../../../../shared/components/tag/tag.component';
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
