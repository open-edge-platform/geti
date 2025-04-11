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
