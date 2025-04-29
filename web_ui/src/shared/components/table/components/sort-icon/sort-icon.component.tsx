// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SortDown, SortUp } from '../../../../../assets/icons';
import { SortDirection } from '../../table.interface';

interface SortIconProps {
    sortDirection: SortDirection;
}

export const SortIcon = ({ sortDirection }: SortIconProps): JSX.Element => {
    if (sortDirection === 'ASC') {
        return <SortUp id='arrow-up-icon' />;
    }

    if (sortDirection === 'DESC') {
        return <SortDown id='arrow-down-icon' />;
    }

    return <></>;
};
