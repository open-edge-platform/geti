// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tag } from '@shared/components/tag/tag.component';

import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './model-card.module.scss';

interface ActiveModelTagProps {
    id: string;
    className?: string;
}

export const ActiveModelTag = ({ id, className = '' }: ActiveModelTagProps): JSX.Element => {
    return (
        <Tag
            withDot={false}
            text='Active model'
            id={`active-model-${idMatchingFormat(id)}-id`}
            data-testid={`active-model-${idMatchingFormat(id)}-id`}
            className={[classes.activeModelTag, className].join(' ')}
        />
    );
};
